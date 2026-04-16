#include <vector>
#include <complex>
#include "LteEngine.hpp"

// C-compatible interface for ctypes
extern "C" {

struct PssRawResults {
    double max_correlation;
    double max_correlation_pss0;
    double max_correlation_pss1;
    double max_correlation_pss2;
    int max_correlation_index;
    int max_correlation_position;
    double frequency_offset;
    int pss_start;
};

// Global engine instance for simplicity in this bridge
static lte::LteEngine* g_engine = nullptr;

void lte_init() {
    if (!g_engine) g_engine = new lte::LteEngine();
}

void lte_cleanup() {
    delete g_engine;
    g_engine = nullptr;
}

PssRawResults lte_detect_pss(const float* iq_real, const float* iq_imag, int num_samples, int fft_bin_size, double sample_rate) {
    lte_init();
    
    std::vector<std::complex<float>> samples(num_samples);
    for (int i = 0; i < num_samples; ++i) {
        samples[i] = {iq_real[i], iq_imag[i]};
    }

    auto res = g_engine->detect_pss(samples, fft_bin_size, sample_rate);
    
    PssRawResults raw_res;
    raw_res.max_correlation = res.max_correlation;
    raw_res.max_correlation_pss0 = res.max_correlation_pss0;
    raw_res.max_correlation_pss1 = res.max_correlation_pss1;
    raw_res.max_correlation_pss2 = res.max_correlation_pss2;
    raw_res.max_correlation_index = res.max_correlation_index;
    raw_res.max_correlation_position = res.max_correlation_position;
    raw_res.frequency_offset = res.frequency_offset;
    raw_res.pss_start = res.pss_start;
    
    return raw_res;
}

}
