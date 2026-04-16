#ifndef LTE_ENGINE_HPP
#define LTE_ENGINE_HPP

#include <vector>
#include <complex>
#include <string>
#include <map>
#include "deps/kissfft/kiss_fft.h"

namespace lte {

struct PssResults {
    double max_correlation;
    double max_correlation_pss0;
    double max_correlation_pss1;
    double max_correlation_pss2;
    int max_correlation_index;
    int max_correlation_position;
    double frequency_offset;
    int pss_start;
};

struct SssResults {
    int N_ID_1;
    int detected_subframe;
};

class LteEngine {
public:
    LteEngine();
    ~LteEngine();

    // Core analysis functions
    PssResults detect_pss(const std::vector<std::complex<float>>& iq_samples, 
                         int fft_bin_size = 2048, 
                         double sample_rate = 30.72e6);

    SssResults detect_sss(const std::vector<std::vector<std::complex<float>>>& grid,
                         int N_ID_2,
                         double frequency_offset,
                         int nRB = 100,
                         double sampling_rate = 30.72e6);

    // Helper functions
    std::vector<std::complex<float>> generate_pss(int N_ID_2);
    std::pair<std::vector<std::complex<float>>, std::vector<std::complex<float>>> generate_sss(int N_ID_1, int N_ID_2);
    
    std::vector<std::vector<std::complex<float>>> get_resource_grid(const std::vector<std::complex<float>>& iq_samples,
                                                                   int pss_start,
                                                                   int fft_bin_size = 2048,
                                                                   int nRB = 100);

private:
    // Internal FFT utilities
    kiss_fft_cfg fft_cfg_2048;
    kiss_fft_cfg ifft_cfg_2048;
};

} // namespace lte

#endif
