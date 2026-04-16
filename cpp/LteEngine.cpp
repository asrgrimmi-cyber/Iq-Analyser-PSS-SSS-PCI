#include "LteEngine.hpp"
#include <cmath>
#include <algorithm>
#include <iostream>
#include <complex>

namespace lte {

const double PI = 3.14159265358979323846;

LteEngine::LteEngine() {
    fft_cfg_2048 = kiss_fft_alloc(2048, 0, nullptr, nullptr);
    ifft_cfg_2048 = kiss_fft_alloc(2048, 1, nullptr, nullptr);
}

LteEngine::~LteEngine() {
    free(fft_cfg_2048);
    free(ifft_cfg_2048);
}

// Port of generate_pss(N_ID_2)
std::vector<std::complex<float>> LteEngine::generate_pss(int N_ID_2) {
    int root;
    if (N_ID_2 == 0) root = 25;
    else if (N_ID_2 == 1) root = 29;
    else if (N_ID_2 == 2) root = 34;
    else return {};

    std::vector<std::complex<float>> pss(62);
    for (int n = 0; n < 31; ++n) {
        float arg = -PI * root * n * (n + 1) / 63.0f;
        pss[n] = std::polar(1.0f, arg);
    }
    for (int n = 31; n < 62; ++n) {
        float arg = -PI * root * (n + 1) * (n + 2) / 63.0f;
        pss[n] = std::polar(1.0f, arg);
    }
    return pss;
}

// Port of DetectPSS
PssResults LteEngine::detect_pss(const std::vector<std::complex<float>>& iq_samples, 
                               int fft_bin_size, 
                               double sample_rate) {
    
    std::vector<std::vector<std::complex<float>>> pss_seqs(3);
    for (int i = 0; i < 3; ++i) pss_seqs[i] = generate_pss(i);

    PssResults res = {0.0, 0.0, 0.0, 0.0, -1, -1, 0.0, 0};
    
    int window_start_idx = (fft_bin_size - 62) / 2;
    int num_samples = iq_samples.size();
    
    kiss_fft_cpx in[2048];
    kiss_fft_cpx out[2048];

    // Sliding window analysis
    // This is the O(N * FFT) part. In C++ it's still fast, but we can parallelize or optimize further.
    for (int j = 0; j < num_samples - fft_bin_size; ++j) {
        // Prepare FFT input
        for (int i = 0; i < fft_bin_size; ++i) {
            in[i].r = iq_samples[j + i].real();
            in[i].i = iq_samples[j + i].imag();
        }
        
        kiss_fft(fft_cfg_2048, in, out);
        
        // FFT Shift manually
        std::vector<std::complex<float>> freq_shifted(fft_bin_size);
        for (int i = 0; i < fft_bin_size; ++i) {
            int src_idx = (i + fft_bin_size / 2) % fft_bin_size;
            freq_shifted[i] = std::complex<float>(out[src_idx].r, out[src_idx].i);
        }

        // Cross correlate with 3 PSS sequences
        for (int k = 0; k < 3; ++k) {
            std::complex<float> correlation(0, 0);
            for (int n = 0; n < 62; ++n) {
                correlation += freq_shifted[window_start_idx + n] * std::conj(pss_seqs[k][n]);
            }
            
            float abs_corr = std::abs(correlation);
            
            if (k == 0 && abs_corr > res.max_correlation_pss0) res.max_correlation_pss0 = abs_corr;
            if (k == 1 && abs_corr > res.max_correlation_pss1) res.max_correlation_pss1 = abs_corr;
            if (k == 2 && abs_corr > res.max_correlation_pss2) res.max_correlation_pss2 = abs_corr;

            if (abs_corr > res.max_correlation) {
                res.max_correlation = abs_corr;
                res.max_correlation_index = k;
                res.max_correlation_position = j;
                res.pss_start = j;
            }
        }
    }

    // Frequency Offset Estimation (simplified port)
    // In Python: frequency_offset_estimation(received_pss, expected_pss, sample_rate)
    // received_pss is from freq_shifted[window_start:end]
    // Let's re-calculate it for the best position
    for (int i = 0; i < fft_bin_size; ++i) {
        in[i].r = iq_samples[res.max_correlation_position + i].real();
        in[i].i = iq_samples[res.max_correlation_position + i].imag();
    }
    kiss_fft(fft_cfg_2048, in, out);
    
    std::complex<double> phase_sum(0, 0);
    auto& best_pss = pss_seqs[res.max_correlation_index];
    for (int n = 0; n < 62; ++n) {
        int src_idx = (window_start_idx + n + fft_bin_size / 2) % fft_bin_size;
        std::complex<float> recv(out[src_idx].r, out[src_idx].i);
        phase_sum += std::complex<double>(recv.real(), recv.imag()) * std::conj(std::complex<double>(best_pss[n].real(), best_pss[n].imag()));
    }
    // Very simplified freq offset estimation for now
    res.frequency_offset = std::arg(phase_sum) * sample_rate / (2.0 * PI * fft_bin_size);

    return res;
}

// Simplified SSS generation (m-sequences)
std::pair<std::vector<std::complex<float>>, std::vector<std::complex<float>>> LteEngine::generate_sss(int N_ID_1, int N_ID_2) {
    // This is a complex mapping of x0, x1 sequences.
    // For brevity in this port, we only placeholder the structure.
    // In a real port, I'd bring the full bit-masking logic from Python.
    std::vector<std::complex<float>> sss0(62, {1, 0}), sss5(62, {1, 0});
    return {sss0, sss5};
}

SssResults LteEngine::detect_sss(const std::vector<std::vector<std::complex<float>>>& grid, 
                               int N_ID_2, double frequency_offset, int nRB, double sampling_rate) {
    SssResults res = {0, 0};
    // Correlation logic for 168 candidates would go here.
    return res;
}

std::vector<std::vector<std::complex<float>>> LteEngine::get_resource_grid(const std::vector<std::complex<float>>& iq_samples,
                                                                          int pss_start, int fft_bin_size, int nRB) {
    // Mapping OFDM symbols to grid
    std::vector<std::vector<std::complex<float>>> grid(14, std::vector<std::complex<float>>(nRB * 12));
    
    // CP lengths for 2048 FFT
    int cp_lengths[] = {160, 144, 144, 144, 144, 144, 144, 160, 144, 144, 144, 144, 144, 144};
    int pss_slot_idx = 6;
    int first_symbol_start = (pss_start - cp_lengths[pss_slot_idx]) - 5 * (cp_lengths[pss_slot_idx] + fft_bin_size) - (cp_lengths[0] + fft_bin_size);
    
    int current_idx = first_symbol_start;
    for (int i = 0; i < 14; ++i) {
        current_idx += cp_lengths[i];
        // FFT of symbol i... (simplified for now)
        current_idx += fft_bin_size;
    }
    
    return grid;
}

} // namespace lte
