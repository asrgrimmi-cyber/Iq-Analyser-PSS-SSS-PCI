#include <iostream>
#include <fstream>
#include <vector>
#include <complex>
#include "LteEngine.hpp"

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: iq_analyzer <file.bin>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Could not open file: " << filename << std::endl;
        return 1;
    }

    // Read IQ samples (complex64 -> 2 floats per sample)
    std::vector<std::complex<float>> samples;
    float real, imag;
    while (file.read(reinterpret_cast<char*>(&real), sizeof(float)) && 
           file.read(reinterpret_cast<char*>(&imag), sizeof(float))) {
        samples.push_back({real, imag});
    }

    std::cout << "Loaded " << samples.size() << " samples from " << filename << std::endl;

    lte::LteEngine engine;
    
    std::cout << "Running PSS Detection..." << std::endl;
    auto pss_res = engine.detect_pss(samples);

    if (pss_res.max_correlation_index != -1) {
        std::cout << "------------------------------------" << std::endl;
        std::cout << "  PSS DETECTION RESULTS (C++)       " << std::endl;
        std::cout << "------------------------------------" << std::endl;
        std::cout << "Detected PSS (N_ID_2): " << pss_res.max_correlation_index << std::endl;
        std::cout << "Max Correlation:       " << pss_res.max_correlation << std::endl;
        std::cout << "Position:              " << pss_res.max_correlation_position << std::endl;
        std::cout << "Frequency Offset:      " << pss_res.frequency_offset << " Hz" << std::endl;
        std::cout << "------------------------------------" << std::endl;
    } else {
        std::cout << "No PSS detected." << std::endl;
    }

    return 0;
}
