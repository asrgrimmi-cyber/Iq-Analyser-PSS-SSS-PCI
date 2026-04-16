"""
IQ Engine — Headless processing pipeline for LTE IQ analysis.
Extracted from iqparser.py main() for use as a library by the Flask app.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless rendering — must be before plt import
import matplotlib.pyplot as plt
import os
import sys

try:
    from cpp_bridge import detect_pss_cpp, is_cpp_available
except ImportError:
    is_cpp_available = lambda: False

# ═══ Plot Styling (Spotify Dark Mode) ═══
plt.rcParams.update({
    'text.color': '#FFFFFF',
    'axes.labelcolor': '#FFFFFF',
    'axes.titlecolor': '#FFFFFF',
    'xtick.color': '#B3B3B3',
    'ytick.color': '#B3B3B3',
    'grid.color': '#444444',
    'grid.alpha': 0.5,
    'figure.facecolor': '#121212',
    'axes.facecolor': '#121212',
    'axes.edgecolor': '#444444'
})

# We need to import iqparser but prevent its monkey-patch from running.
# The monkey-patch runs at module level (lines 16-135), so we override plt.show
# after import to use our own save logic.


def analyze_iq_file(bin_path, session_id, output_dir="static/images"):
    """
    Runs the full PSS → SSS → PCI → CRS → Equalization pipeline.

    Args:
        bin_path: Path to the .bin IQ file (complex64 format)
        session_id: Unique ID for this analysis session
        output_dir: Base directory for saving plot images

    Returns:
        dict with 'parameters' (detected values) and 'plots' (image paths + titles)
    """
    # Import processing functions — this triggers iqparser module load
    from iqparser import (
        resample_iq, DetectPSS, getResourceGrid, DetectSSS, getPCI,
        generate_pss, generate_sss, ShowPSS, ShowGrid, ShowSSS,
        GetCRSandChannelCoef, ShowCRS, cloneArray, setResourceGrid,
        plotGridImage, interpolateGrid, ShowResourceGridIQ,
        ShowResourceGridMagPhase, ResourceGridDiv, calculate_detailed_power_metrics
    )

    session_dir = os.path.join(output_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Collector for plots
    plots = []
    plot_counter = [0]

    def save_plot(title="Untitled"):
        """Save the current matplotlib figure with given title."""
        plot_counter[0] += 1
        clean = "".join([c if c.isalnum() else "_" for c in str(title)])
        filename = f"{plot_counter[0]:02d}_{clean}.png"
        filepath = os.path.join(session_dir, filename)
        try:
            plt.savefig(filepath, dpi=150, bbox_inches='tight',
                        facecolor='#1e1e2e', edgecolor='none')
        except Exception:
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close('all')
        web_path = f"/static/images/{session_id}/{filename}"
        plots.append({"title": str(title), "path": web_path})

    # Override plt.show so all Show* functions from iqparser save to disk
    original_show = plt.show

    def intercepted_show(*args, **kwargs):
        """Intercept plt.show() calls — save figure instead of displaying."""
        fig = plt.gcf()
        title_text = "Untitled"
        if fig._suptitle:
            title_text = fig._suptitle.get_text()
        elif fig.axes:
            t = fig.axes[0].get_title()
            if t:
                title_text = t
        save_plot(title_text)

    plt.show = intercepted_show

    parameters = {}

    try:
        # ── Load IQ samples ──
        with open(bin_path, 'rb') as f:
            iq_samples = np.fromfile(f, dtype=np.complex64)

        # ── Resample 23.04 MHz → 30.72 MHz ──
        iq_samples = resample_iq(iq_samples, orig_rate=23.04e6, target_rate=30.72e6)

        sample_rate = 30.72e6
        fft_bin_size = 2048
        NRB = 100

        # ── PSS Detection (C++ Accelerated or Python Fallback) ──
        if is_cpp_available():
            print(">>> Using C++ Accelerated PSS Detection")
            resultsPSS_raw = detect_pss_cpp(iq_samples, fft_bin_size, sample_rate)
            
            # Post-process for complex data needed for plotting (from original iq_samples)
            pss_start = resultsPSS_raw['pss_start']
            iq_window = iq_samples[pss_start : pss_start + fft_bin_size]
            frequency_samples = np.fft.fft(iq_window, fft_bin_size)
            frequency_samples = np.fft.fftshift(frequency_samples)
            window_start = (fft_bin_size - 62) // 2
            
            resultsPSS = {
                'max_correlation_index': resultsPSS_raw['max_correlation_index'],
                'max_correlation': resultsPSS_raw['max_correlation'],
                'max_correlation_pss0': resultsPSS_raw['max_correlation_pss0'],
                'max_correlation_pss1': resultsPSS_raw['max_correlation_pss1'],
                'max_correlation_pss2': resultsPSS_raw['max_correlation_pss2'],
                'max_correlation_position': resultsPSS_raw['max_correlation_position'],
                'frequency_offset': resultsPSS_raw['frequency_offset'],
                'pss_start': pss_start,
                'max_window_samples': frequency_samples[window_start : window_start + 62],
                'pss_time_domain': np.abs(iq_window)
            }
            
            # Extract 14 OFDM symbols (logic reused from Python DetectPSS results)
            # Re-running the logic here avoids duplicate code in engine vs bridge for now
            # To be fully optimal, this should also move to C++.
            from iqparser import DetectPSS
            temp_res = DetectPSS(iq_samples, fft_bin_size, sample_rate) # Still used for symbol extraction mapping
            resultsPSS['ofdm_symbols'] = temp_res['ofdm_symbols'] 

        else:
            print(">>> Using Python PSS Detection (Fallback)")
            resultsPSS = DetectPSS(iq_samples, fft_bin_size, sample_rate, debug=False)

        parameters['Detected PSS Sequence (N_ID_2)'] = int(resultsPSS["max_correlation_index"])
        parameters['Maximum Correlation'] = f'{resultsPSS["max_correlation"]:.6f}'
        parameters['Max Correlation PSS0'] = f'{resultsPSS["max_correlation_pss0"]:.6f}'
        parameters['Max Correlation PSS1'] = f'{resultsPSS["max_correlation_pss1"]:.6f}'
        parameters['Max Correlation PSS2'] = f'{resultsPSS["max_correlation_pss2"]:.6f}'
        parameters['Position of Max Correlation'] = int(resultsPSS["max_correlation_position"])
        parameters['Estimated Frequency Offset'] = f'{resultsPSS["frequency_offset"]:.2f} Hz'

        max_correlation_index = resultsPSS["max_correlation_index"]
        pss_start = resultsPSS["pss_start"]
        pss_time_domain = resultsPSS["pss_time_domain"]
        ofdm_symbols = resultsPSS["ofdm_symbols"]
        detected_pss_freq_domain = resultsPSS["max_window_samples"]
        frequency_offset = resultsPSS["frequency_offset"]

        # ── Resource Grid ──
        resourceGrid = getResourceGrid(ofdm_symbols, nRB=NRB, removeDC=True)
        parameters['Resource Grid Dimension'] = f'{resourceGrid.shape}'

        # ── SSS Detection ──
        N_ID_2 = max_correlation_index
        resultsSSS = DetectSSS(resourceGrid, N_ID_2, frequency_offset,
                               nRB=NRB, samplingRate=sample_rate, debug=False)

        N_ID_1 = resultsSSS["N_ID_1"]
        sss_no_correction = resultsSSS["sss_no_correction"]
        sss_corrected = resultsSSS["sss_corrected"]
        detected_subframe = resultsSSS["detected_subframe"]

        parameters['Detected Subframe'] = int(detected_subframe)
        parameters['Detected N_ID_2 (PSS)'] = int(N_ID_2)
        parameters['Detected N_ID_1 (SSS)'] = int(N_ID_1)

        PCI = getPCI(N_ID_1, N_ID_2)
        parameters['Detected PCI'] = int(PCI)

        # ── Generate Plots ──

        # Plot 1: PSS Detection
        ShowPSS(iq_samples, detected_pss_freq_domain, max_correlation_index,
                ofdm_symbols, pss_start, pss_time_domain)
        # ShowPSS calls plt.show() internally, which triggers intercepted_show

        # Plot 2: Resource Grid
        ShowGrid(ofdm_symbols, nRB=NRB, zmin=-25, zmax=0)

        # Plot 3: SSS Analysis
        ShowSSS(sss_no_correction, sss_corrected, N_ID_1, N_ID_2, detected_subframe)

        # ── CRS & Channel Estimation ──
        crs_rx, crs_ex, h, crs_k = GetCRSandChannelCoef(
            resourceGrid, PCI, nRB=100, method="generate", subframe=0, debug=False)

        # Plot 4: CRS Constellation
        ShowCRS(crs_rx, crs_ex, h)

        # Build h Resource Grid
        hResourceGrid = cloneArray(resourceGrid, 0.0 + 1j * 0.0)
        hResourceGrid = setResourceGrid(hResourceGrid, symb=0, k_list=crs_k[0], v_list=h[0])
        hResourceGrid = setResourceGrid(hResourceGrid, symb=4, k_list=crs_k[1], v_list=h[1])
        hResourceGrid = setResourceGrid(hResourceGrid, symb=7, k_list=crs_k[2], v_list=h[2])
        hResourceGrid = setResourceGrid(hResourceGrid, symb=11, k_list=crs_k[3], v_list=h[3])

        # ── Power & Noise Analysis ──
        power_metrics = calculate_detailed_power_metrics(resourceGrid, crs_rx, crs_ex, h, nRB=100)
        parameters.update(power_metrics)

        # Plot 5: Raw Channel Grid
        plotGridImage(hResourceGrid)

        # Interpolate
        hResourceGrid_interpolated = interpolateGrid(
            hResourceGrid, mode=0, td_method="interpolate", direction="ccw")

        # Plot 6: Interpolated Channel Grid
        plotGridImage(hResourceGrid_interpolated)

        # Plot 7: Interpolated H I/Q
        ShowResourceGridIQ(hResourceGrid_interpolated,
                          figTitle="Interpolated [h] Grid I/Q", figTitleColor="#1DB954")

        # Plot 8: Channel Magnitude/Phase
        ShowResourceGridMagPhase(hResourceGrid_interpolated)

        # Equalization
        resourceGrid_corrected = ResourceGridDiv(resourceGrid, hResourceGrid_interpolated)
        if np.any(np.isnan(resourceGrid_corrected)) or np.any(np.isinf(resourceGrid_corrected)):
            resourceGrid_corrected = np.clip(resourceGrid_corrected, -20, 20)

        # Plot 9: Before Equalization
        ShowResourceGridIQ(resourceGrid, clip=20,
                          figTitle="Before Equalization", figTitleColor="#1DB954")

        # Plot 10: After Equalization
        ShowResourceGridIQ(resourceGrid_corrected, clip=10,
                          figTitle="After Equalization", figTitleColor="#1DB954")

    finally:
        plt.show = original_show

    return {
        "parameters": parameters,
        "plots": plots,
    }


# Allow direct testing: python iq_engine.py
if __name__ == "__main__":
    import json
    test_bin = "lte_20Mhz_rate23.04Mhz_dur_10ms_pci252_traffic/lte_20Mhz_rate23.04Mhz_dur_10ms_pci252_traffic.bin"
    if os.path.exists(test_bin):
        results = analyze_iq_file(test_bin, "test_session")
        print(json.dumps(results, indent=2))
    else:
        print(f"Test file not found: {test_bin}")
