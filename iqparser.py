import numpy as np
import matplotlib.pyplot as plt
import struct
import matplotlib.gridspec as gridspec
from scipy.signal import butter, lfilter
from scipy.signal import resample_poly
from scipy import interpolate
from scipy.interpolate import interp1d
from scipy.interpolate import CubicSpline
from scipy.signal import resample
import cmath

import os
import time

# --- BEGIN MONKEY PATCH FOR HTML DASHBOARD ---
os.makedirs('static/images', exist_ok=True)
original_show = plt.show

image_files = []
plot_counter = 0
gui_parameters = {}

def update_html():
    param_html = ""
    if gui_parameters:
        param_html = "<div class='card parameters-card'><div class='card-header'><h3>Detected Parameters</h3></div><div class='card-body'><div class='param-grid'>"
        for k, v in gui_parameters.items():
            param_html += f"<div class='param-item'><span class='param-label'>{k}:</span> <span class='param-value'>{v}</span></div>"
        param_html += "</div></div></div>"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IQ Analyzer Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{
                font-family: 'Inter', sans-serif;
                background: #0f172a;
                color: #f8fafc;
                margin: 0;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            h1 {{
                text-align: center;
                font-weight: 800;
                font-size: 3rem;
                margin-bottom: 50px;
                background: linear-gradient(135deg, #38bdf8, #818cf8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 4px 20px rgba(56, 189, 248, 0.2);
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
                gap: 40px;
                margin-top: 20px;
            }}
            .card {{
                background: rgba(30, 41, 59, 0.7);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease, border-color 0.3s ease;
            }}
            .card:hover {{
                transform: translateY(-8px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
                border-color: rgba(56, 189, 248, 0.4);
            }}
            .parameters-card {{
                grid-column: 1 / -1;
                background: rgba(15, 23, 42, 0.8);
                border-color: rgba(56, 189, 248, 0.3);
            }}
            .parameters-card .card-header {{
                background: rgba(56, 189, 248, 0.1);
            }}
            .card-header {{
                padding: 20px 25px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                background: rgba(15, 23, 42, 0.5);
            }}
            .card-header h3 {{
                margin: 0;
                font-size: 1.25rem;
                font-weight: 600;
                color: #e2e8f0;
            }}
            .card-body {{
                padding: 25px;
            }}
            .param-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
            }}
            .param-item {{
                padding: 12px 15px;
                background: rgba(255, 255, 255, 0.03);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.05);
                display: flex;
                flex-direction: column;
                gap: 5px;
            }}
            .param-label {{
                color: #94a3b8;
                font-weight: 600;
                font-size: 0.95rem;
            }}
            .param-value {{
                color: #38bdf8;
                font-weight: 800;
                font-family: monospace;
                font-size: 1.1rem;
            }}
            .card-image {{
                padding: 20px;
                background: white; /* Images have white background */
            }}
            .card-image img {{
                width: 100%;
                height: auto;
                display: block;
                border-radius: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>IQ Analyzer Dashboard</h1>
            <div class="grid">
                {param_html}
                {"".join(f'<div class="card"><div class="card-header"><h3>{t}</h3></div><div class="card-image"><img src="{f}" alt="{t}" loading="lazy"></div></div>' for t, f in image_files)}
            </div>
        </div>
    </body>
    </html>
    """
    with open('index.html', 'w') as f:
        f.write(html_content)

def set_gui_parameter(key, value):
    gui_parameters[key] = value
    update_html()

def custom_show():
    global plot_counter
    plot_counter += 1
    fig = plt.gcf()
    title = fig._suptitle.get_text() if fig._suptitle else f"Plot {plot_counter}"
    clean_title = "".join([c if c.isalnum() else "_" for c in title])
    
    filename = f"static/images/{plot_counter:02d}_{clean_title}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close('all')
    image_files.append((title, filename))
    update_html()

plt.show = custom_show
# --- END MONKEY PATCH ---


class ComplexOps:
    def __init__(self):
        pass
    

    def interpolate(self, c1, c2, numPoints, direction='ccw'):
        points = []
        step = 1 / (numPoints - 1)
        r1, phi1 = abs(c1), cmath.phase(c1)
        r2, phi2 = abs(c2), cmath.phase(c2)
        
        if direction == 'cw':
            while phi2 > phi1:
                phi2 -= 2 * np.pi
        else:
            while phi2 < phi1:
                phi2 += 2 * np.pi
 
        for i in range(numPoints):
            t = i * step
            r = r1 + (r2 - r1) * t
            phi = phi1 + (phi2 - phi1) * t
            points.append(cmath.rect(r, phi))
        return points
    
    def getPhaseStep(self, c1, c2, numPoints, nStep = 1, direction='ccw'):
        points = []
        step = 1 / (numPoints - 1)
        r1, phi1 = abs(c1), cmath.phase(c1)
        r2, phi2 = abs(c2), cmath.phase(c2)
        if direction == 'cw':
            while phi2 > phi1:
                phi2 -= 2 * np.pi
        else:
            while phi2 < phi1:
                phi2 += 2 * np.pi
        
        return np.exp(1j * nStep* ((phi2 - phi1)/numPoints))
    
    def interpolate_colinear(self, c1, c2, numPoints):
        points = []
        step = 1 / (numPoints - 1)
        
        real1, imag1 = c1.real, c1.imag
        real2, imag2 = c2.real, c2.imag
        
        for i in range(numPoints):
            t = i * step
            real_interpolated = real1 + (real2 - real1) * t
            imag_interpolated = imag1 + (imag2 - imag1) * t
            points.append(complex(real_interpolated, imag_interpolated))
        
        return points

    

    def extrapolate(self, c1, c2, numPoints, direction='ccw'):
        points = []
        step = 1 / (numPoints - 1)
        r1, phi1 = abs(c1), cmath.phase(c1)
        r2, phi2 = abs(c2), cmath.phase(c2)
        if direction == 'cw':
            while phi2 > phi1:
                phi2 -= 2 * np.pi
        else:
            while phi2 < phi1:
                phi2 += 2 * np.pi
        for i in range(numPoints):
            t = i * step
            r = r2 + (r2 - r1) * t
            phi = phi2 + (phi2 - phi1) * t
            points.append(cmath.rect(r, phi))
        return points
    

    def quadratic_fit(self, c1, c2, c3):
        x = np.array([0, 1, 2])
        mag = np.array([abs(c1), abs(c2), abs(c3)])
        phase = np.array([cmath.phase(c1), cmath.phase(c2), cmath.phase(c3)])
        z_mag = np.polyfit(x, mag, 2)
        z_phase = np.polyfit(x, phase, 2)
        return z_mag, z_phase
    
 
    def extrapolate_3pt(self, c1, c2, c3, numPoints=10):
        mags = [abs(c1), abs(c2), abs(c3)]
        phases = [cmath.phase(c) for c in [c1, c2, c3]]
        dmags = [mags[1]-mags[0], mags[2]-mags[1]]
        dphases = [phases[1]-phases[0], phases[2]-phases[1]]
        dmag_avg = np.mean(dmags)
        dphase_avg = np.mean(dphases)
        extrapolated = []
        last_mag = mags[-1]
        last_phase = phases[-1]
        for _ in range(numPoints):
            new_mag = last_mag + dmag_avg
            new_phase = last_phase + dphase_avg
            extrapolated.append(cmath.rect(new_mag, new_phase))
            last_mag = new_mag
            last_phase = new_phase
        return extrapolated
    

def generate_pss(n_id_2):

    u_shift = [25, 29, 34] # Root Zadoff-Chu sequence numbers

    d_u = []

    for n in range(62):  
        u = u_shift[n_id_2]

        if n <= 30:
            d = np.exp(-1j * np.pi * u * n * (n + 1) / 63)  
        else:
            d = np.exp(-1j * np.pi * u * (n + 1) * (n + 2) / 63)  
        
        d_u.append(d)

    return np.array(d_u)


def frequency_offset_estimation(received_pss, expected_pss, sample_rate = 30.72e6):

    phase_difference = np.angle(np.dot(received_pss, np.conj(expected_pss)))
    
    # Time duration for transmitting PSS, in seconds
    time_duration_pss = 62 / sample_rate

    # Convert phase difference to frequency offset in Hz
    frequency_offset = (phase_difference / (2 * np.pi)) / time_duration_pss 

    return frequency_offset


def correct_frequency_offset(signal, frequency_offset, sample_rate, debug = False):

    signal = np.array(signal, dtype=np.complex128)
    #time = np.arange(len(signal)) / sample_rate
    time = len(signal) / sample_rate
    correction = np.exp(-1j * 2 * np.pi * frequency_offset * time)
    corrected_signal = signal * correction

    # just for debugging
    if debug :
        print("[Debug Info] correct_frequency_offset() -------------------")
        print("[Debug Info] Frequency Offset ==> ",frequency_offset)
        print("[Debug Info] sample_rate ==> ",sample_rate)
        original_signal_magnitude = np.abs(signal)
        corrected_signal_magnitude = np.abs(corrected_signal)
        # Check if the original signal magnitude and corrected signal magnitude are the same
        print("[Debug Info] comparison of mag : ", np.allclose(original_signal_magnitude, corrected_signal_magnitude))
        print("[Debug Info] correction : ", correction , "angle : ", np.angle(correction))

    return corrected_signal


def manual_resample(iq_samples, orig_rate, target_rate):
    # Calculate the number of original and resampled points
    orig_points = np.arange(len(iq_samples))
    resample_ratio = target_rate / orig_rate
    num_samples = int(len(iq_samples) * resample_ratio)
    resampled_points = np.linspace(orig_points.min(), orig_points.max(), num_samples)

    # Create an interpolator function
    interpolator = interpolate.interp1d(orig_points, iq_samples, kind='linear', fill_value="extrapolate")

    # Generate the resampled complex signal
    resampled_iq_samples = interpolator(resampled_points)

    return resampled_iq_samples


def resample_iq(iq_samples, orig_rate=23.04e6, target_rate=30.72e6):

    # Calculate the number of samples in the resampled signal
    resample_ratio = target_rate / orig_rate
    num_samples = int(len(iq_samples) * resample_ratio)
    
    # Resample the IQ samples
    resampled_iq = resample(iq_samples, num_samples)
    #resampled_iq = manual_resample(iq_samples, orig_rate, target_rate)

    return resampled_iq


def cloneArray(ary, init):
    # Determine the shape of the input array
    shape = ary.shape
    
    # Create a new array with the same shape and initialize with the given value
    cAry = np.full(shape, init)
    
    return cAry

def generate_sss(NID1,NID2):

    q_prime = np.floor(NID1/30)
    q = np.floor(((NID1+q_prime*(q_prime+1)/2))/30)
    m_prime = NID1 + q *(q+1)/2
    m0 = m_prime % 31
    m1 = (m0 + np.floor(m_prime/31) + 1) % 31

    # generate d_even() sequence
    x_s = np.zeros(31)
    x_s[:5] = [0, 0, 0, 0, 1]
    for i in range(26):
        x_s[i+5] = (x_s[i+2] + x_s[i]) % 2

    x_c = np.zeros(31)
    x_c[:5] = [0, 0, 0, 0, 1]
    for i in range(26):
        x_c[i+5] = (x_c[i+3] + x_c[i]) % 2

    s_tilda = 1 - 2*x_s
    c_tilda = 1 - 2*x_c
    s0_m0_even = np.zeros(31)
    s1_m1_even = np.zeros(31)
    for n in range(31):
        s0_m0_even[n] = s_tilda[int((n+m0)%31)]
        s1_m1_even[n] = s_tilda[int((n+m1)%31)]

    c0_even = np.zeros(31)
    for n in range(31):
        c0_even[n] = c_tilda[int((n+NID2)%31)]

    d_even_sub0 = s0_m0_even * c0_even
    d_even_sub5 = s1_m1_even * c0_even

    # generate d_odd() sequence
    x_z = np.zeros(31)
    x_z[:5] = [0, 0, 0, 0, 1]
    for i in range(26):
        x_z[i+5] = (x_z[i+4] + x_z[i+2] + x_z[i+1] + x_z[i]) % 2

    z_tilda = 1 - 2*x_z
    s1_m1_odd = np.zeros(31)
    s0_m0_odd = np.zeros(31)
    for n in range(31):
        s1_m1_odd[n] = s_tilda[int((n+m1)%31)]
        s0_m0_odd[n] = s_tilda[int((n+m0)%31)]

    c1_odd = np.zeros(31)
    for n in range(31):
        c1_odd[n] = c_tilda[int((n+NID2+3)%31)]

    z1_m0_odd = np.zeros(31)
    z1_m1_odd = np.zeros(31)
    for n in range(31):
        z1_m0_odd[n] = z_tilda[int((n+m0%8)%31)]
        z1_m1_odd[n] = z_tilda[int((n+m1%8)%31)]

    d_odd_sub0 = s1_m1_odd * c1_odd * z1_m0_odd
    d_odd_sub5 = s0_m0_odd * c1_odd * z1_m1_odd

    # calculate d_sub0
    d_sub0 = np.zeros(62)
    d_sub0[::2] = d_even_sub0
    d_sub0[1::2] = d_odd_sub0
    sss0 = d_sub0

    d_sub5 = np.zeros(62)
    d_sub5[::2] = d_even_sub5
    d_sub5[1::2] = d_odd_sub5
    sss5 = d_sub5

    return sss0, sss5


class LteCRS:
    def __init__(self, Nc=1600, Ncp=1, NID=252, ns=0, l=0, NRB=100, debug=False):
        self.Nc = Nc 
        self.Ncp = Ncp
        self.NRBmax = 110
        self.max_m = 12 * self.NRBmax   # Maximum possible value of m.
        self.x1 = np.zeros(self.max_m + self.Nc + 32, dtype=np.int32)
        self.x2 = np.zeros(self.max_m + self.Nc + 32, dtype=np.int32)
        self.cseq = []
        self.NID = NID
        self.ns = ns
        self.l = l
        self.NRB = NRB
        
        self.debug = debug

        if self.debug == True : 
            print(f'[Debug] LteCRS() -> NID = {self.NID}')
            print(f'[Debug] LteCRS() -> ns = {self.ns}')
            print(f'[Debug] LteCRS() -> l = {self.l}')
            print(f'[Debug] LteCRS() -> Ncp = {self.Ncp}')
            print(f'[Debug] LteCRS() -> Nc = {self.Nc}')
            print(f'[Debug] LteCRS() -> NRB = {self.NRB}')

    def x2_init(self, seed):
        SEQUENCE_SEED_LEN = 31  # length of the seed
        for i in range(SEQUENCE_SEED_LEN):
            if ((seed >> i) & 1):   # taking out bits from LSB
                if self.debug == True : print(f'setting 1 at x2[{i}]')
                self.x2[i] = 1

        binary_seed = format(seed, 'b').zfill(SEQUENCE_SEED_LEN)
        if self.debug == True : print(f'[Debug] x2_init() -> binary_seed = {binary_seed}')

        # Assign each bit of the binary seed to the x2 array
        for i in range(SEQUENCE_SEED_LEN):
            #self.x2[i] = int(binary_seed[i])
            self.x2[i] = int(binary_seed[SEQUENCE_SEED_LEN-i-1])        
               

    def cinit(self):
        c_init = (2**10) * (7*(self.ns + 1) + self.l + 1) * (2*self.NID + 1) + 2*self.NID + self.Ncp
        if self.debug == True : print(f'[Debug] cinit() -> cinit = {c_init}')
        return c_init

    def c(self, n):
        return (self.x1[n + self.Nc] + self.x2[n + self.Nc]) % 2
        #return (self.x1[n + self.Nc - 1] + self.x2[n + self.Nc - 1]) % 2


    def x1_next(self, n):
        self.x1[n + 31] = (self.x1[n + 3] + self.x1[n]) % 2

    def x2_next(self, n):
        self.x2[n + 31] = (self.x2[n + 3] + self.x2[n + 2] + self.x2[n + 1] + self.x2[n]) % 2

    def r(self, m):
        c_even = self.c(2 * m)
        c_odd = self.c(2 * m + 1)
        self.cseq.append(c_even)
        self.cseq.append(c_odd)
        real = (1 / np.sqrt(2)) * (1 - 2 * c_even)
        imag = (1 / np.sqrt(2)) * (1 - 2 * c_odd)
        return real + 1j*imag

    def generate_sequences(self):
        # Initialize x1 and x2 sequences
        self.x1[0] = 1
        self.x2_init(self.cinit())

        # generate x1 and x2 sequences
        #for n in range(self.Nc + 1):
        for n in range(self.max_m + self.Nc + 1):    
            self.x1_next(n)
            self.x2_next(n)
        
        # Define the range of m
        m_values = np.arange(2 * self.NRB)
        m_p_values = m_values + self.NRBmax - self.NRB

        # Generate r sequence
        #r_sequence = [self.r(m) for m in m_values]
        r_sequence = [self.r(m_p) for m_p in m_p_values]
        
        if self.debug == True : print("[Debug] generate_sequences() -> c_seq (", len(self.cseq),") = ", self.cseq)
        # Return the r sequence
        return r_sequence


    def print_info(self):
        # Calculate and print binary representation
        result = self.cinit()
        print("[Info] cinit=",result)
        binary_result = bin(result)[2:] 
        print("[Info] cinit in binary=",binary_result)

        # Take the last 32 elements and convert to string
        binary_str = ''.join(map(str, self.x2[:32]))
        print("[Info] x2 init in binary =", binary_str)
        # Reverse the binary string to properly align the bits
        reversed_binary_str = binary_str[::-1]
        # Convert the reversed binary string to an integer
        x2_init_dec = int(reversed_binary_str, 2)
        print("[Info] x2 init in decimal =", x2_init_dec)

        print("[Info] length of x1 =", len(self.x1))
        print("[Info] length of x2 =", len(self.x2))
        print(f"[Info] cinit: {self.cinit()}")
        
        # Define the range of m
        m_values = np.arange(2 * self.NRB)
        r_sequence = [self.r(m) for m in m_values]
        #print("r_sequence = ", r_sequence)

    def lte_generate_prs_c(self, c_init, seq_len):
        x1 = np.zeros(1600 + seq_len, dtype=int)
        x2 = np.zeros(1600 + seq_len, dtype=int)
        tmp = c_init
        
        for n in range(31):
            x2[30-n] = tmp // (2**(30-n))
            tmp = tmp - (x2[30-n] * 2**(30-n))
        x1[0] = 1

        for n in range(1600 + seq_len - 31):  
            x1[n+31] = (x1[n+3] + x1[n]) % 2
            #x2[n+31] = (x2[n+3] + x2[n+2] + 2*x2[n+1]) % 2
            x2[n+31] = (x2[n+3] + x2[n+2] + x2[n+1] + + x2[n]) % 2

        c = np.zeros(seq_len, dtype=int)
        for n in range(seq_len):
            c[n] = (x1[n+1600] + x2[n+1600]) % 2

        return c

    def lte_generate_crs(self):

        N_s = self.ns
        L = self.l
        N_id_cell = self.NID

        if not (0 <= N_s <= 19):
            print("ERROR: Invalid N_s ({})".format(N_s))
            return [0]
        if not (0 <= L <= 6):
            print("ERROR: Invalid L ({})".format(L))
            return [0]
        if not (0 <= N_id_cell <= 503):
            print("ERROR: Invalid N_id_cell ({})".format(N_id_cell))
            return [0]

        #N_cp = 1
        #N_cp = self.Ncp
        N_rb_dl_max = self.NRB
        #c_init = 1024 * (7 * (N_s+1) + L + 1) * (2 * N_id_cell + 1) + 2*N_id_cell + N_cp
        c_init = self.cinit()
        len_ = 2 * N_rb_dl_max
        if self.debug == True : print("[Debug] lte_generate_crs() -> c_init=",c_init)

        c = self.lte_generate_prs_c(c_init, 2*(len_-1)+2)

        r = np.zeros(len_, dtype=complex)
        for m in range(len_):
            r[m] = (1/np.sqrt(2)) * (1 - 2*c[2*m]) + 1j * (1/np.sqrt(2)) * (1 - 2*c[2*m+1])

        return r
    

    def getHardcodedCRS(self) :

       # this is test vector generated with following condition
       # PCI=252, NRB=100, ns = {0,1}, l = {0,4} ==> OFDM cymbol {0,4,7,11}
       # verified working with IQ/lte_20Mhz_rate23.04Mhz_dur_10ms_pci252_traffic_agc.bin
        crs0 = [-0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j]

        crs4 = [ 0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j]

        crs7 = [ 0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j]


        crs11=[-0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678+0.70710678j,
       -0.70710678+0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678-0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j,  0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678+0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j,
        0.70710678-0.70710678j,  0.70710678-0.70710678j,
       -0.70710678+0.70710678j, -0.70710678+0.70710678j,
        0.70710678+0.70710678j, -0.70710678-0.70710678j,
       -0.70710678-0.70710678j, -0.70710678-0.70710678j]

        return crs0, crs4, crs7, crs11


def cross_correlate(a, b):
    return np.sum(a * np.conj(b))


# refer to https://www.sharetechnote.com/html/Handbook_LTE_PhyParameter_DL_FDD.html 
def DetectPSS(iq_samples, fft_bin_size=2048, sample_rate=30.72e6, debug=False):

    # just for debugging
    if debug :
        print("[Debug Info] DetectPSS() -------------------")

    pss_seqs = [generate_pss(i) for i in range(3)]

    max_correlation = 0
    max_window_samples = None
    max_correlation_index = None
    max_correlation_position = None

    max_correlation_pss0 = max_correlation_pss1 = max_correlation_pss2 = 0

    for j in range(len(iq_samples) - fft_bin_size):
        iq_window = iq_samples[j : j + fft_bin_size]
        frequency_samples = np.fft.fft(iq_window, fft_bin_size)
        frequency_samples = np.fft.fftshift(frequency_samples)

        for k in range(3):
            # window_samples = frequency_samples[993:1055] (PSS REs for 20 Mhz)
            # Calculate the start and end of the window
            window_start = (fft_bin_size - 62) // 2
            window_end = window_start + 62
            window_samples = frequency_samples[window_start:window_end]

            correlation = np.sum(window_samples * np.conj(pss_seqs[k]))

            if k == 0 and abs(correlation) > max_correlation_pss0:
                max_correlation_pss0 = abs(correlation)
            elif k == 1 and abs(correlation) > max_correlation_pss1:
                max_correlation_pss1 = abs(correlation)
            elif k == 2 and abs(correlation) > max_correlation_pss2:
                max_correlation_pss2 = abs(correlation)

            if abs(correlation) > max_correlation:
                max_correlation = abs(correlation)
                max_correlation_index = k
                max_correlation_position = j
                max_window_samples = window_samples
                pss_start = j
                pss_time_domain = np.abs(iq_window)

    # Calculate Frequency Offset
    iq_window = iq_samples[max_correlation_position : max_correlation_position + fft_bin_size]
    frequency_samples = np.fft.fft(iq_window, fft_bin_size)
    frequency_samples = np.fft.fftshift(frequency_samples)
    half_bin = fft_bin_size // 2
    start_index = half_bin - 31  # 31 is half of the PSS length (62)
    end_index = half_bin + 31
    received_pss = frequency_samples[start_index:end_index]
    #received_pss = frequency_samples[993:1055]
    expected_pss = pss_seqs[max_correlation_index]
    frequency_offset = frequency_offset_estimation(received_pss, expected_pss,sample_rate)
    
    # Specify the cyclic prefix lengths for each OFDM symbol in a slot
    if fft_bin_size == 2048 : 
        cp_lengths = [160, 144, 144, 144, 144, 144, 144, 160, 144, 144, 144, 144, 144, 144]
    elif fft_bin_size == 1536 : 
        cp_lengths = [120, 108, 108, 108, 108, 108, 108, 120, 108, 108, 108, 108, 108, 108]
    elif fft_bin_size == 1024 : 
        cp_lengths = [80, 72, 72, 72, 72, 72, 72, 80, 72, 72, 72, 72, 72, 72]
    elif fft_bin_size == 512 : 
        cp_lengths = [40, 36, 36, 36, 36, 36, 36, 40, 36, 36, 36, 36, 36, 36]
    elif fft_bin_size == 256 : 
        cp_lengths = [20, 18, 18, 18, 18, 18, 18, 20, 18, 18, 18, 18, 18, 18]
    elif fft_bin_size == 128 : 
        cp_lengths = [10, 9, 9, 9, 9, 9, 9, 10, 9, 9, 9, 9, 9, 9]
    pss_slot_index = 6

    # Calculate the start position of the first OFDM symbol by adding up the CP lengths
    first_symbol_start = (pss_start - cp_lengths[pss_slot_index]) - 5 * (cp_lengths[pss_slot_index]+fft_bin_size) - (cp_lengths[0]+fft_bin_size) 

    # Check if there are enough samples before and after PSS
    if pss_start >= first_symbol_start + 6 * fft_bin_size and pss_start + 8 * fft_bin_size <= len(iq_samples):
        # Extract 14 OFDM symbols where PSS is located, taking into account the CP
        ofdm_symbols = []
        start_index = first_symbol_start
        for i in range(14):
            start_index = start_index + cp_lengths[i]
            end_index = start_index + fft_bin_size
            ofdm_symbols.append(iq_samples[start_index : end_index])
            # just for debugging
            if debug :
                print("[Debug Info] ODFM symbol : ", i, ", start_index : ",start_index, ", end_index : ",end_index, ", sample length : ",len(ofdm_symbols[i]))
            start_index = end_index
        ofdm_symbols = np.array(ofdm_symbols)
    else:
        print("Not enough samples to extract 14 OFDM symbols.")


    return {
        'max_correlation': max_correlation, 
        'max_correlation_pss0': max_correlation_pss0, 
        'max_correlation_pss1': max_correlation_pss1, 
        'max_correlation_pss2': max_correlation_pss2, 
        'max_correlation_index': max_correlation_index, 
        'max_correlation_position': max_correlation_position, 
        'frequency_offset': frequency_offset,
        'max_window_samples': max_window_samples, 
        'ofdm_symbols': ofdm_symbols, 
        'pss_start' : pss_start,
        'pss_time_domain' : pss_time_domain ,      
    }


def getREs(resourceGrid, symNo, scList):

    try:
        # Retrieve the REs corresponding to the given symbol number and subcarrier indices
        return [resourceGrid[symNo][sc] for sc in scList]
    except IndexError:
        print("Invalid symbol number or subcarrier index")
        return []


def ShowPSS(iq_samples, detected_pss_freq_domain, max_correlation_index, ofdm_symbols, pss_start, pss_time_domain, fft_bin_size = 2048):

    import matplotlib.pyplot as plt
    import numpy as np

    # Create a single figure
    fig = plt.figure(figsize=(15, 9))

    # Create the left side subplots
    ax1 = plt.subplot2grid((7, 3), (0, 0), rowspan=2, colspan=1)
    ax3 = plt.subplot2grid((7, 3), (2, 0), rowspan=2, colspan=1)
    ax4 = plt.subplot2grid((7, 3), (4, 0), rowspan=2, colspan=1)
    ax5 = plt.subplot2grid((7, 3), (6, 0), rowspan=1, colspan=1)

    # Frequency Spectrum of IQ samples
    fft_iq_samples = np.fft.fft(iq_samples)
    fft_iq_samples = np.fft.fftshift(fft_iq_samples)
    fft_iq_samples_db = 20 * np.log10(np.abs(fft_iq_samples))
    ax1.plot(fft_iq_samples_db)
    ax1.set_title('Frequency Spectrum of IQ samples (dB scale)', fontsize=8)
    ax1.grid(True)
    ax1.set_xlabel('Frequency', fontsize=8)
    ax1.set_ylabel('Amplitude (dB)', fontsize=8)
    ax1.tick_params(axis='both', labelsize=8)

    # Frequency Spectrum of Detected PSS
    fft_detected_pss = np.fft.fft(detected_pss_freq_domain)
    # Normalize by dividing all elements by the maximum magnitude
    fft_detected_pss_normalized = fft_detected_pss / np.abs(fft_detected_pss).max()

    # Plot the Detected PSS
    ax3.scatter(fft_detected_pss_normalized.real, fft_detected_pss_normalized.imag, label='Detected PSS')
    # Normalized PSS data
    normalized_data = fft_detected_pss / np.abs(fft_detected_pss)
    # Plot the Normalized data
    ax3.scatter(normalized_data.real, normalized_data.imag, label='Normalized PSS', alpha=0.5)
    ax3.legend()
    ax3.grid(True)
    ax3.set_title('IQ Constellation of Detected PSS and Normalized PSS', fontsize=8)
    ax3.set_xlabel('In-Phase (I)', fontsize=8)
    ax3.set_ylabel('Quadrature (Q)', fontsize=8)
    ax3.legend(fontsize=8)
    ax3.tick_params(axis='both', labelsize=8)

    # Generate the PSS for the detected PCI
    generated_pss = generate_pss(max_correlation_index)
    # IQ plot of the generated PSS
    ax4.scatter(generated_pss.real, generated_pss.imag)
    ax4.grid(True)
    ax4.set_title('IQ Constellation of Generated PSS for NID2='+str(max_correlation_index), fontsize=8)
    ax4.set_xlabel('In-Phase (I)', fontsize=8)
    ax4.set_ylabel('Quadrature (Q)', fontsize=8)
    ax4.tick_params(axis='both', labelsize=8)

    # Frequency Spectrum of IQ samples
    mag_iq_samples = np.abs(iq_samples)
    ax5.plot(mag_iq_samples)
    ax5.plot(range(pss_start, pss_start + len(pss_time_domain)), pss_time_domain, label='Detected PSS', linestyle='--')
    ax5.grid(True)
    ax5.set_title('IQ in time doman and Detected PSS', fontsize=8)
    ax5.set_xlabel('Time', fontsize=8)
    ax5.set_ylabel('Amplitude', fontsize=8)
    ax5.legend(fontsize=8)
    ax5.tick_params(axis='both', labelsize=8)

    # Create the right side subplots
    axs = [plt.subplot2grid((7, 3), (i % 7, i // 7 + 1)) for i in range(14)]

    # Code to generate the plots for axs
    for i in range(14):
        ax = axs[i]
        symbol = ofdm_symbols[i]
        freq_domain_symbol = np.fft.fft(symbol, fft_bin_size)
        freq_domain_symbol = np.fft.fftshift(freq_domain_symbol)
        freq_domain_symbol = freq_domain_symbol / np.max(np.abs(freq_domain_symbol))
        freq_domain_symbol_db = 20 * np.log10(np.abs(freq_domain_symbol))
        ax.plot(freq_domain_symbol_db)
        ax.set_ylim([-50, 0])

    plt.tight_layout()
    plt.show() 



def ShowGrid(ofdm_symbols, nRB = 100, zmin=-25, zmax=0):
 
    # Calculate the magnitude of the OFDM symbols
    frequency_domain_symbols = np.fft.fft(ofdm_symbols, axis=1)
    frequency_domain_symbols = np.fft.fftshift(frequency_domain_symbols, axes=1)

    # Compute the magnitude of the frequency domain symbols
    magnitude = np.abs(frequency_domain_symbols)
    magnitude = magnitude / np.max(magnitude, axis=1, keepdims=True)

    # Convert to decibels and normalize
    magnitude_db = 20 * np.log10(magnitude + np.finfo(float).eps)

    # Number of subcarriers
    total_subcarriers = frequency_domain_symbols.shape[1]

    # Calculate the start and end index for the desired number of RBs
    start_index = (total_subcarriers - nRB * 12) // 2
    end_index = start_index + nRB * 12

    # Slice the magnitude_db array to include only the desired RBs
    magnitude_db = magnitude_db[:, start_index:end_index]

    # Create a figure and an axes object
    fig, ax = plt.subplots(figsize=(14, 5))
    
    # Use the imshow function to create the 2D graph
    cax = ax.imshow(magnitude_db, aspect='auto', cmap='RdBu_r', interpolation='none', vmin=zmin, vmax=zmax)

    # Create a color bar to show the mapping between values and colors
    fig.colorbar(cax)
    
    # Add labels and title
    ax.set_xlabel("Subcarriers")
    ax.set_ylabel("OFDM Symbols")
    ax.set_title("Resource Grid")

    # Set y-axis labels for every symbol
    symbol_labels = ['Symbol {}'.format(i) for i in range(ofdm_symbols.shape[0])]
    ax.set_yticks(np.arange(ofdm_symbols.shape[0]))
    ax.set_yticklabels(symbol_labels)

    # Adjust x-axis ticks and labels to start from 0 and go up to nRB*12 with step size of 12
    ax.set_xticks(np.arange(0, nRB * 12 + 1, 12*5))
    ax.set_xticklabels(np.arange(0, nRB * 12 + 1, 12*5))

    # Display the graph
    plt.tight_layout() 
    plt.show()


def ShowGridIQ(ofdm_symbols, nRB = 100):
    # Calculate the magnitude of the OFDM symbols
    frequency_domain_symbols = np.fft.fft(ofdm_symbols, axis=1)
    frequency_domain_symbols = np.fft.fftshift(frequency_domain_symbols, axes=1)
    # Number of subcarriers
    total_subcarriers = frequency_domain_symbols.shape[1]

    # Calculate the start and end index for the desired number of RBs
    start_index = (total_subcarriers - nRB * 12) // 2
    end_index = start_index + nRB * 12

    # Slice the frequency_domain_symbols array to include only the desired RBs
    resource_grid = frequency_domain_symbols[:, start_index:end_index]

    # Create the I and Q values from the complex numbers
    I_values = resource_grid.real
    Q_values = resource_grid.imag

    fig, axs = plt.subplots(4, 4, figsize=(12,9))  # 3 rows, 4 columns

    for i in range(14):
        # Assign a subplot to each OFDM symbol
        row = i // 4
        col = i % 4
        #c = axs[row, col].scatter(I_values[i, :], Q_values[i, :], c=np.arange(len(I_values[i, :])), cmap='bwr', s=5)
        c = axs[row, col].scatter(I_values[i, :], Q_values[i, :], s = 5)
        axs[row, col].set_title(f'OFDM symbol {i}')
        axs[row, col].set_xlabel('In-phase (I)')
        axs[row, col].set_ylabel('Quadrature (Q)')

        # Calculate the minimum and maximum of I and Q values for this OFDM symbol
        I_min, I_max = np.min(I_values[i, :]), np.max(I_values[i, :])
        Q_min, Q_max = np.min(Q_values[i, :]), np.max(Q_values[i, :])
        #print("Symb = ",i,"I_min = ", I_min, "I_max = ", I_max," Q_min = ", Q_min, "Q_max = ", Q_max)

        s = 1.2
        max = np.max([I_max,Q_max])
        axs[row, col].set_xlim([-s*max, s*max])
        axs[row, col].set_ylim([-s*max, s*max])
        #fig.colorbar(c, ax=axs[row, col])

    plt.tight_layout()
    plt.show()




def ShowResourceGridIQ(resourceGrid, clip="auto", figTitle="Resource Grid IQ", figTitleColor="red", data_range = 'all'):

    # Slice the frequency_domain_symbols array to include only the desired RBs
    resource_grid = resourceGrid

    # Create the I and Q values from the complex numbers
    I_values = resource_grid.real
    Q_values = resource_grid.imag

    if data_range != 'all' :
        I_values = I_values[:,data_range[0]:data_range[1]]
        Q_values = Q_values[:,data_range[0]:data_range[1]]

    print('No of Data = ', len(I_values[0]))
    fig, axs = plt.subplots(4, 4, figsize=(12,9))  
    fig.suptitle(figTitle, color=figTitleColor,weight='bold')

    for i in range(14):
        # Assign a subplot to each OFDM symbol
        row = i // 4
        col = i % 4
        #c = axs[row, col].scatter(I_values[i, :], Q_values[i, :], c=np.arange(len(I_values[i, :])), cmap='bwr', s=5)
        c = axs[row, col].scatter(I_values[i, :], Q_values[i, :], s = 5)
        axs[row, col].set_title(f'OFDM symbol {i}')
        axs[row, col].set_xlabel('In-phase (I)')
        axs[row, col].set_ylabel('Quadrature (Q)')

        # Calculate the minimum and maximum of I and Q values for this OFDM symbol
        I_min, I_max = np.min(I_values[i, :]), np.max(I_values[i, :])
        Q_min, Q_max = np.min(Q_values[i, :]), np.max(Q_values[i, :])
        #print("Symb = ",i,"I_min = ", I_min, "I_max = ", I_max," Q_min = ", Q_min, "Q_max = ", Q_max)

        s = 1.2
        if clip == "auto" :            
            max = np.max([I_max,Q_max])            
        else:
            max = clip 

        if max > 0:
            axs[row, col].set_xlim([-s*max, s*max])
            axs[row, col].set_ylim([-s*max, s*max])    


    plt.tight_layout()
    plt.show()


def ResourceGridDiv(ResourceGrid1, ResourceGrid2):
    # Check for zero values in ResourceGrid2 and replace with 1 to prevent division by zero
    # (this will return a result of ResourceGrid1 for those positions)
    ResourceGrid2_safe = np.where(ResourceGrid2 != 0, ResourceGrid2, 1)
    
    # Element-wise division
    threshold = 1e-10  # or some other small number
    ResourceGrid2_safe[np.abs(ResourceGrid2_safe) < threshold] = threshold
    
    resultGrid = ResourceGrid1 / ResourceGrid2_safe
    
    return resultGrid


def getResourceGrid(ofdm_symbols, nRB = 100, removeDC=False):
    # Calculate the magnitude of the OFDM symbols
    frequency_domain_symbols = np.fft.fft(ofdm_symbols, axis=1)
    frequency_domain_symbols = np.fft.fftshift(frequency_domain_symbols, axes=1)

    # Number of subcarriers
    total_subcarriers = frequency_domain_symbols.shape[1]

    # Calculate the start and end index for the desired number of RBs
    start_index = (total_subcarriers - nRB * 12) // 2
    end_index = start_index + nRB * 12

    # Slice the frequency_domain_symbols array to include only the desired RBs
    resource_grid = frequency_domain_symbols[:, start_index:end_index]

    # Remove the DC subcarrier resource elements if requested
    if removeDC:
        dc_index = resource_grid.shape[1] // 2
        resource_grid = np.delete(resource_grid, dc_index, axis=1)

    return resource_grid


def getCrsPos(N_cellID, NRB, l, p, ns):
    vshift = N_cellID % 6
    if p == 0:
        if l % 7 == 0:
            v = 0
        else:
            v = 3
    elif p == 1:
        if l == 0:
            v = 3
        else:
            v = 0
    elif p == 2:
        v = 3 * (ns % 2)
    elif p == 3:
        v = 3 + 3 * (ns % 2)
    else:
        raise ValueError("Invalid value of p")

    m_values = range(2 * NRB)  # m = 0,1,...,(2*NRB-1)
    k_values = [6 * m + (v + vshift) % 6 for m in m_values]

    return k_values


def DetectSSS(resourceGrid, N_ID_2, frequency_offset, nRB = 100, samplingRate = 30.72e6, debug = False):
    if debug :
        print("[Debug Info] DetectSSS() ---------------- ") 
        print("[Debug Info] Frequency Offset ==> ",frequency_offset)
        print("[Debug Info] N_ID_2 ==> ",N_ID_2)

    # Generate the list of subcarrier indices for SSS
    noOfRE = nRB * 12
    sss_sc_indices = list(range(noOfRE-noOfRE//2-31, noOfRE-noOfRE//2+31))

    # Extract SSS for the first and second slots
    sss_no_correction = getREs(resourceGrid, 5, sss_sc_indices)

    # Apply frequency offset correction to the extracted SSS
    #sss = np.array(sss_no_correction)
    sss = correct_frequency_offset(sss_no_correction, frequency_offset, samplingRate, debug)
    #sss = sss_no_correction

    # Calculate correlations for all possible N_ID_1
    max_corr = -np.inf
    best_N_ID_1 = None
    for N_ID_1 in range(168):
        # Generate expected SSS
        expected_sss0, expected_sss5 = generate_sss(N_ID_1, N_ID_2)
        # Calculate correlation
        corr0 = np.abs(cross_correlate(sss, expected_sss0))
        corr5 = np.abs(cross_correlate(sss, expected_sss5))
        total_corr = max(corr0, corr5)
        if debug :
            print("[Debug Info] corr0 = ", corr0, ",corr5 = ", corr5, ", N_ID_1 = ", N_ID_1)

        # If this correlation is the highest we've seen, save it and the current N_ID_1
        if total_corr > max_corr:
            max_corr = total_corr
            best_N_ID_1 = N_ID_1
            if debug :
                print("[Debug Info] corr0 = ", corr0, ", corr5 = ", corr5, ", max_corr = ", max_corr, ", N_ID_1 = ", N_ID_1)

    if debug :
        print('[Debug Info] Detected SSS (N_ID_1): ', best_N_ID_1)

    # Detect the subframe (0 or 5) based on the correlation results
    detected_subframe = 0 if cross_correlate(sss, generate_sss(best_N_ID_1, N_ID_2)[0]) > cross_correlate(sss, generate_sss(best_N_ID_1, N_ID_2)[1]) else 5

    return {
        'sss_no_correction': sss_no_correction, 
        'sss_corrected': sss, 
        'N_ID_1': best_N_ID_1, 
        'detected_subframe': detected_subframe,
    }


def getPCI(N_ID_1, N_ID_2) :
    return 3*N_ID_1 + N_ID_2


def ShowSSS(sss_no_correction, sss_corrected, N_ID_1, N_ID_2,detected_subframe):

    sss_generated = np.array(generate_sss(N_ID_1, N_ID_2))
    if detected_subframe == 0 :
        sss_generated = sss_generated[0]
    else :
        sss_generated = sss_generated[1]    

    sss_no_correction = np.array(sss_no_correction, dtype=np.complex128)
    sss_corrected = np.array(sss_corrected, dtype=np.complex128)
    
    # Normalize sss_no_correction and sss_corrected
    sss_no_correction = sss_no_correction / np.mean(np.abs(sss_no_correction))
    sss_corrected = sss_corrected / np.mean(np.abs(sss_corrected))

    data_list = [sss_no_correction, sss_corrected, sss_generated ]
    #print("[Debug Info] ==> " , data_list)
    titles = ['sss_no_correction', 'sss_corrected', 'sss from N_ID_1']
    fig, axs = plt.subplots(3, 3, figsize=(9, 9))

    for i, data in enumerate(data_list):
        # Ensure data is a numpy array with complex numbers
        data = np.array(data, dtype=np.complex128)

        axs[0, i].scatter(data.real, data.imag, color='b')  
        axs[0, i].set_title(f'{titles[i]}', fontsize=8)
        axs[0, i].set_xlabel('Real', fontsize=8)
        axs[0, i].set_ylabel('Imaginary', fontsize=8)
        axs[0, i].tick_params(axis='both', which='major', labelsize=8)
        axs[0, i].set_xlim(-2,2)
        axs[0, i].set_ylim(-2,2)

        axs[1, i].plot(data.real)
        axs[1, i].set_title(f'{titles[i]}', fontsize=8)
        axs[1, i].set_xlabel('Data Index', fontsize=8)
        axs[1, i].set_ylabel('Real', fontsize=8)
        axs[1, i].tick_params(axis='both', which='major', labelsize=8)
        axs[1, i].set_ylim(-2,2)

        axs[2, i].plot(data.imag)
        axs[2, i].set_title(f'{titles[i]}', fontsize=8)
        axs[2, i].set_xlabel('Data Index', fontsize=8)
        axs[2, i].set_ylabel('Imaginary', fontsize=8)
        axs[2, i].tick_params(axis='both', which='major', labelsize=8)
        axs[2, i].set_ylim(-2,2)

    plt.tight_layout()
    plt.show()


def getRSRP(signal):
    # Ensure the signal is a numpy array for easier calculations
    signal = np.array(signal)
    if len(signal) == 0: return -140.0

    # Calculate the power of the signal
    power = np.mean(np.abs(signal)**2)

    # Return the power in dBm (relative to FS)
    if power <= 0: return -140.0
    return 10 * np.log10(power)


def calculate_detailed_power_metrics(resource_grid, crs_rx, crs_ex, h, nRB=100):
    """
    Calculates RSRP, RSSI, RSRQ, and SNR based on CRS and Resource Grid.
    """
    # 1. RSSI: Total wideband power
    rssi_linear = np.mean(np.abs(resource_grid)**2)
    rssi_dbm = 10 * np.log10(rssi_linear) if rssi_linear > 0 else -140.0

    # 2. RSRP: Average power of CRS symbols
    # Flatten all received CRS samples
    all_crs_rx = np.concatenate([np.array(x) for x in crs_rx])
    rsrp_dbm = getRSRP(all_crs_rx)

    # 3. RSRQ: (N * RSRP) / RSSI
    # N is the number of Resource Blocks (RB)
    rsrq_db = -20.0 # default
    if rssi_linear > 0:
        rsrp_linear = np.mean(np.abs(all_crs_rx)**2)
        # RSRQ = N * RSRP / RSSI (Standard LTE formula)
        rsrq_linear = (nRB * 12 * rsrp_linear) / (rssi_linear * 12 * nRB) # simplified to rsrp/rssi mapping
        # Standard formula often uses: RSRQ = N * RSRP / RSSI
        # Here N is number of RBs. Specifically, it's (N x 12 x RSRP) / RSSI
        rsrq_db = 10 * np.log10(rsrp_linear / rssi_linear) + 10 * np.log10(1) # Simplified RSRQ
    
    # 4. SNR Estimation
    # SNR = Signal Power / Noise Power
    # We estimate Noise Power from the variance of the channel estimation residuals
    # (Received CRS - (Channel * Expected CRS))
    noise_samples = []
    for i in range(len(crs_rx)):
        rx = np.array(crs_rx[i])
        ex = np.array(crs_ex[i])
        hi = np.array(h[i])
        # Residual error after channel estimation
        # This is a rough SNR estimate
        error = rx - (hi * ex)
        noise_samples.extend(error)
    
    noise_linear = np.mean(np.abs(noise_samples)**2)
    signal_linear = np.mean(np.abs(all_crs_rx)**2)
    
    snr_db = 0.0
    if noise_linear > 0:
        snr_db = 10 * np.log10(signal_linear / noise_linear)
    
    return {
        'RSRP (dBFS)': f"{rsrp_dbm:.2f}",
        'RSSI (dBFS)': f"{rssi_dbm:.2f}",
        'RSRQ (dB)': f"{rsrq_db:.2f}",
        'SNR (dB)': f"{snr_db:.2f}",
        'Noise Floor (dBFS)': f"{10 * np.log10(noise_linear):.2f}" if noise_linear > 0 else "-140"
    }


# calculate the channel coefficient corresponding to each CRS and return the recieved CRS (crs_rx), channel coefficient (h) and 
# the list of subcarrier number for crs (crs_k). All of these crs_rx, h, crs_k would carry the data for symbol 0,4,7,11 of the 
# subframe in resourceGrid 
def GetCRSandChannelCoef(resourceGrid,PCI,nRB = 100, method = "generate", subframe=0, debug=False) :

    crs_rx = []
    crs_ex = []
    h = []
    crs_k = []
    dbg = True
    ns_offset = subframe*2

    if method == "generate" :
        ltecrs = LteCRS(NID=PCI, ns=ns_offset+0, l=0, NRB=nRB, debug=dbg)
        crs0 = ltecrs.generate_sequences()
        ltecrs.print_info()
        ltecrs = LteCRS(NID=PCI, ns=ns_offset+0, l=4, NRB=nRB, debug=dbg)
        crs4 = ltecrs.generate_sequences()
        ltecrs.print_info()
        ltecrs = LteCRS(NID=PCI, ns=ns_offset+1, l=0, NRB=nRB, debug=dbg)
        crs7 = ltecrs.generate_sequences()
        ltecrs.print_info()
        ltecrs = LteCRS(NID=PCI, ns=ns_offset+1, l=4, NRB=nRB, debug=dbg)
        crs11 = ltecrs.generate_sequences()
        ltecrs.print_info()

        ltecrs = LteCRS(NID=PCI, ns=ns_offset+0, l=0, NRB=nRB, debug=dbg)
        crs0_ = ltecrs.lte_generate_crs()

        ltecrs = LteCRS(NID=PCI, ns=ns_offset+0, l=4, NRB=nRB, debug=dbg)
        crs4_ = ltecrs.lte_generate_crs()

        ltecrs = LteCRS(NID=PCI, ns=ns_offset+1, l=0, NRB=nRB, debug=dbg)
        crs7_ = ltecrs.lte_generate_crs()

        ltecrs = LteCRS(NID=PCI, ns=ns_offset+1, l=4, NRB=nRB, debug=dbg)
        crs11_ = ltecrs.lte_generate_crs()

    if method == "testvector" :
        ltecrs = LteCRS()
        crs0, crs4, crs7, crs11 = ltecrs.getHardcodedCRS()

    if debug == True :
        # Using array_equal
        are_equal = np.array_equal(crs0, crs0_)
        print(f"[Debug] GetCRSandChannelCoef() -> Are exactly equal (crs0 == crs0_): {are_equal}")

        # Using allclose
        tolerance = 1e-3
        are_almost_equal = np.allclose(crs0, crs0_, atol=tolerance)
        print(f"[Debug] GetCRSandChannelCoef() -> Are almost equal within a tolerance of {tolerance}: {are_almost_equal}")

        are_equal = np.array_equal(crs4, crs4_)
        print(f"[Debug] GetCRSandChannelCoef() -> Are exactly equal (crs4 == crs4_): {are_equal}")

        # Using allclose
        tolerance = 1e-3
        are_almost_equal = np.allclose(crs4, crs4_, atol=tolerance)
        print(f"[Debug] GetCRSandChannelCoef() -> Are almost equal within a tolerance of {tolerance}: {are_almost_equal}")

        are_equal = np.array_equal(crs7, crs7_)
        # are_equal = np.array_equal(crs11, crs11_)
        print(f"[Debug] GetCRSandChannelCoef() -> Are exactly equal (crs7 == crs7_): {are_equal}")

        # Using allclose
        tolerance = 1e-3
        are_almost_equal = np.allclose(crs7, crs7_, atol=tolerance)
        print(f"[Debug] GetCRSandChannelCoef() -> Are almost equal within a tolerance of {tolerance}: {are_almost_equal}")

        are_equal = np.array_equal(crs11, crs11_)
        print(f"[Debug] GetCRSandChannelCoef() -> Are exactly equal (crs11 == crs11_): {are_equal}")

        # Using allclose
        tolerance = 1e-3
        are_almost_equal = np.allclose(crs11, crs11_, atol=tolerance)
        print(f"[Debug] GetCRSandChannelCoef() -> Are almost equal within a tolerance of {tolerance}: {are_almost_equal}")

    
    # process for CRS at OFDM symbol 0
    symNo = 0
    k_list = getCrsPos(PCI,nRB,l=symNo,p=0,ns=0) # calculate all the resource element position for CRS at the specified OFDM symbol
    offset = 0
    k_list = [k + offset for k in k_list] # shifting the calculated position by offset. this is mainly for debugging purpose.
    crs_list = getREs(resourceGrid, symNo, k_list)  # retrieve resource element value specified in k_list
    crs0_chest = np.array(crs_list) / np.array(crs0)  # calculate the channel coefficient. 
    crs_rx.append(crs_list)  # store the array of the extracted CRS value to the variable crs_rx
    crs_ex.append(np.array(crs0))  # store the array of the generated CRS value to the variable crs_ex
    h.append(crs0_chest) # store the array of the extracted h coefficient to the variable h
    crs_k.append(k_list) # store the array of the calculated crs resource element position to the variable crs_k
    

    # process for CRS at OFDM symbol 4
    symNo = 4
    k_list = getCrsPos(PCI,nRB,l=symNo,p=0,ns=0) 
    offset = 0
    k_list = [k + offset for k in k_list]
    crs_list = getREs(resourceGrid, symNo, k_list)
    crs4_chest = np.array(crs_list) / np.array(crs4)
    crs_rx.append(crs_list)
    crs_ex.append(np.array(crs4)) 
    h.append(crs4_chest)
    crs_k.append(k_list)

    # process for CRS at OFDM symbol 7
    symNo = 7
    k_list = getCrsPos(PCI,nRB,l=symNo,p=0,ns=1) 
    offset = 0
    k_list = [k + offset for k in k_list]
    crs_list = getREs(resourceGrid, symNo, k_list)
    crs7_chest = np.array(crs_list) / np.array(crs7)
    crs_rx.append(crs_list)
    crs_ex.append(np.array(crs7)) 
    h.append(crs7_chest)
    crs_k.append(k_list)

    # process for CRS at OFDM symbol 11
    symNo = 11
    k_list = getCrsPos(PCI,nRB,l=symNo,p=0,ns=1) 
    offset = 0
    k_list = [k + offset for k in k_list]
    crs_list = getREs(resourceGrid, symNo, k_list)
    crs11_chest = np.array(crs_list) / np.array(crs11)
    crs_rx.append(crs_list)
    crs_ex.append(np.array(crs11)) 
    h.append(crs11_chest)
    crs_k.append(k_list)

    return crs_rx, crs_ex, h, crs_k



def ShowCRS(crs_rx, crs_ex, h) :

    I_values_sym0 = [x.real for x in crs_rx[0]]  # get the real part (In-phase)
    Q_values_sym0 = [x.imag for x in crs_rx[0]]  # get the imaginary part (Quadrature)
    I_values_sym0_ex = [x.real for x in crs_ex[0]]  # get the real part (In-phase)
    Q_values_sym0_ex = [x.imag for x in crs_ex[0]]  # get the imaginary part (Quadrature)
    rsrp0 = getRSRP(crs_rx[0])
    crs0_chest = h[0]
    I_values_crs0_chest = [x.real for x in crs0_chest]  # get the real part (In-phase)
    Q_values_crs0_chest = [x.imag for x in crs0_chest]  # get the imaginary part (Quadrature)
    

    I_values_sym4 = [x.real for x in crs_rx[1]]  # get the real part (In-phase)
    Q_values_sym4 = [x.imag for x in crs_rx[1]]  # get the imaginary part (Quadrature)
    I_values_sym4_ex = [x.real for x in crs_ex[1]]  # get the real part (In-phase)
    Q_values_sym4_ex = [x.imag for x in crs_ex[1]]  # get the imaginary part (Quadrature)
    rsrp4 = getRSRP(crs_rx[1])
    crs4_chest = h[1]
    I_values_crs4_chest = [x.real for x in crs4_chest]  # get the real part (In-phase)
    Q_values_crs4_chest = [x.imag for x in crs4_chest]  # get the imaginary part (Quadrature)

    I_values_sym7 = [x.real for x in crs_rx[2]]  # get the real part (In-phase)
    Q_values_sym7 = [x.imag for x in crs_rx[2]]  # get the imaginary part (Quadrature)
    I_values_sym7_ex = [x.real for x in crs_ex[2]]  # get the real part (In-phase)
    Q_values_sym7_ex = [x.imag for x in crs_ex[2]]  # get the imaginary part (Quadrature)
    rsrp7 = getRSRP(crs_rx[2])
    crs7_chest = h[0]
    I_values_crs7_chest = [x.real for x in crs7_chest]  # get the real part (In-phase)
    Q_values_crs7_chest = [x.imag for x in crs7_chest]  # get the imaginary part (Quadrature)

    I_values_sym11 = [x.real for x in crs_rx[3]]  # get the real part (In-phase)
    Q_values_sym11 = [x.imag for x in crs_rx[3]]  # get the imaginary part (Quadrature)
    I_values_sym11_ex = [x.real for x in crs_ex[3]]  # get the real part (In-phase)
    Q_values_sym11_ex = [x.imag for x in crs_ex[3]]  # get the imaginary part (Quadrature)
    rsrp11 = getRSRP(crs_rx[3])
    crs11_chest = h[3]
    I_values_crs11_chest = [x.real for x in crs11_chest]  # get the real part (In-phase)
    Q_values_crs11_chest = [x.imag for x in crs11_chest]  # get the imaginary part (Quadrature)


    fig, axs = plt.subplots(4, 5, figsize=(14,9) )  # 1 row, 3 columns
    plt.rcParams.update({'font.size': 7})

    # Array of symbol numbers
    symbol_numbers = [0, 4, 7, 11]

    # Array of I_values and Q_values
    I_values = [I_values_sym0, I_values_sym4, I_values_sym7, I_values_sym11]
    Q_values = [Q_values_sym0, Q_values_sym4, Q_values_sym7, Q_values_sym11]
    I_values_ex = [I_values_sym0_ex, I_values_sym4_ex, I_values_sym7_ex, I_values_sym11_ex]
    Q_values_ex = [Q_values_sym0_ex, Q_values_sym4_ex, Q_values_sym7_ex, Q_values_sym11_ex]
    I_values_chest = [I_values_crs0_chest, I_values_crs4_chest, I_values_crs7_chest, I_values_crs11_chest]
    Q_values_chest = [Q_values_crs0_chest, Q_values_crs4_chest, Q_values_crs7_chest, Q_values_crs11_chest]
    rsrp = [rsrp0, rsrp4,rsrp7,rsrp11]

    # Loop over each symbol number
    font_size = 7
    for i in range(4):
        # Constellation Plot
        colors = range(len(I_values[i]))
        axs[i, 0].scatter(I_values[i], Q_values[i], c=colors, cmap='bwr')
        axs[i, 0].set_title(f'crs_rx : symNo = {symbol_numbers[i]}, rsrp={rsrp[i]:.2f}', fontsize=font_size)
        axs[i, 0].tick_params(axis='both', which='major', labelsize=font_size)
        axs[i, 0].grid(True)

        # I sequence Plot
        axs[i, 1].plot(I_values[i], color='r')
        axs[i, 1].set_title(f'I sequence for symNo = {symbol_numbers[i]}', fontsize=font_size)
        axs[i, 1].tick_params(axis='both', which='major', labelsize=font_size)
        axs[i, 1].grid(True)

        # Q sequence Plot
        axs[i, 2].plot(Q_values[i], color='g')
        axs[i, 2].set_title(f'Q sequence for symNo = {symbol_numbers[i]}', fontsize=font_size)
        axs[i, 2].tick_params(axis='both', which='major', labelsize=font_size)
        axs[i, 2].grid(True)

        # Constellation Plot
        colors = range(len(I_values_ex[i]))
        axs[i, 3].scatter(I_values_ex[i], Q_values_ex[i], c=colors, cmap='bwr')
        axs[i, 3].set_title(f'crs_ex : symNo = {symbol_numbers[i]}', fontsize=font_size)
        axs[i, 3].tick_params(axis='both', which='major', labelsize=font_size)
        axs[i, 3].grid(True)

        colors = range(len(I_values_chest[i]))
        axs[i, 4].scatter(I_values_chest[i], Q_values_chest[i], c=colors, cmap='bwr')
        axs[i, 4].set_title(f'h=crs_rx/crx_ex : symNo = {symbol_numbers[i]}', fontsize=font_size)
        axs[i, 4].tick_params(axis='both', which='major', labelsize=font_size)
        axs[i, 4].grid(True)    

    plt.tight_layout()
    plt.show()


def setResourceGrid(resourceGrid, symb, k_list, v_list):
    
    if len(k_list) != len(v_list):
        raise ValueError("k_list and v_list must have the same length.")
    
    # Setting the values
    for k, v in zip(k_list, v_list):
        resourceGrid[symb, k] = v
    
    return resourceGrid



def complex_moving_average(data, window_size=7):

    # Create a kernel of ones
    kernel = np.ones(window_size) / window_size

    # Convolve real and imaginary parts separately
    real_convolved = np.convolve(data.real, kernel, mode='full')
    imag_convolved = np.convolve(data.imag, kernel, mode='full')

    # Trim the convolution result
    start_trim = (window_size - 1) // 2
    end_trim = -(window_size - 1) // 2 if window_size % 2 == 0 else -((window_size - 1) // 2) 

    real_trimmed = real_convolved[start_trim:end_trim]
    imag_trimmed = imag_convolved[start_trim:end_trim]

    return real_trimmed + 1j * imag_trimmed


def interpolateGrid(resourceGrid, window_size=6, mode = 0, td_method='copy',direction="ccw"):

    symbols, subcarriers = resourceGrid.shape
    resultGrid = np.empty_like(resourceGrid, dtype=complex)
    resultGrid = resourceGrid
    interpolator = ComplexOps()
    
    # if mode == 0 interpolate both time and frequency domain
    # if mode == 1 interpolate frequency domain only
    # if mode == 2 interpolate domain only
    # if mode == 3 no interpolation

    # frequence domain interpolation
    if (mode == 0) or (mode == 1) : 
        print("Interpolate in Frequency Domain")
        for i in range(symbols):
            ofdm_symbol = resourceGrid[i]
            resultGrid[i] = complex_moving_average(ofdm_symbol, window_size)

    # time domain interpolate : different methods is applied based on td_method
    if (mode == 0) or (mode == 2) : 
        print("Interpolate in Time Domain")
        if td_method =='copy' :
            # For each subcarrier
            for k in range(resourceGrid.shape[1]):
                # Copy symbol 0 to symbols 1, 2, and 3
                resultGrid[1:4, k] = resultGrid[0, k]
                # Copy symbol 4 to symbols 5 and 6
                resultGrid[5:7, k] = resultGrid[4, k]
                # Copy symbol 7 to symbols 8, 9, and 10
                resultGrid[8:11, k] = resultGrid[7, k]
                # Copy symbol 11 to symbols 12 and 13
                resultGrid[12:14, k] = resultGrid[11, k]
        
        if td_method =='interpolate' :
            for k in range(resourceGrid.shape[1]):

                # Interpolation for symbols 5,6 using symbols 4 and 7 as endpoints
                interpolated_points = interpolator.interpolate(resourceGrid[0, k], resourceGrid[4, k], 5, direction)
                resultGrid[1:4, k] = interpolated_points[1:4]

                # Interpolation for symbols 5,6 using symbols 4 and 7 as endpoints
                interpolated_points = interpolator.interpolate(resourceGrid[4, k], resourceGrid[7, k], 4, direction)
                resultGrid[5:7, k] = interpolated_points[1:3]

                # Interpolation for symbols 8,9,10 using symbols 7 and 11 as endpoints
                interpolated_points = interpolator.interpolate(resourceGrid[7, k], resourceGrid[11, k], 5, direction)
                resultGrid[8:11, k] = interpolated_points[1:4]

                # Extrapolation for symbols 12,13 using symbols 9, 10, 11 as initial points
                extrapolated_points = interpolator.extrapolate_3pt(resourceGrid[9, k], resourceGrid[10, k], resourceGrid[11, k],5)
                resultGrid[12:14, k] = extrapolated_points[:2]   

        
    return resultGrid




def plotGridImage(resourceGrid):
    # Calculate magnitude for better visualization
    magnitude = np.abs(resourceGrid)

    plt.figure(figsize=(14, 5))
    plt.imshow(magnitude, aspect='auto', origin='lower', cmap='inferno')
    plt.colorbar(label='Magnitude')
    plt.xlabel('Subcarrier Index')
    plt.title('Resource Grid Image')
    
    # Set y-axis labels for every symbol
    symbol_labels = ['Symbol {}'.format(i) for i in range(resourceGrid.shape[0])]
    plt.yticks(np.arange(resourceGrid.shape[0]), symbol_labels)
    plt.tight_layout()
    plt.show()


def ShowResourceGridMagPhase(resourceGrid):
    #num_subcarriers, num_ofdm_symbols = resourceGrid.shape
    num_symbols, num_subcarriers  = resourceGrid.shape
    colors = plt.cm.jet(np.linspace(0, 1, num_symbols))  # Create a color map
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))  # Create a 2x1 subplot

    # Aggregate data for easier plotting
    magnitudes = np.abs(resourceGrid)
    phases = np.angle(resourceGrid)
    
    # Plot Magnitudes
    for l in range(num_symbols):
        ax[0].plot( magnitudes[l,:], color=colors[l], label=f'Symbol {l}')
    ax[0].set_title('Magnitude of OFDM Symbols')
    ax[0].set_xlabel('Subcarrier Number')
    ax[0].set_ylabel('Magnitude')
    ax[0].legend(loc='upper right')
    
    # Plot Phases
    for l in range(num_symbols):
        ax[1].plot( phases[l,:], color=colors[l], label=f'Symbol {l}')
    ax[1].set_title('Phase of OFDM Symbols')
    ax[1].set_xlabel('Subcarrier Number')
    ax[1].set_ylabel('Phase (Radians)')
    ax[1].legend(loc='upper right')
    
    plt.tight_layout()
    plt.show()



def ShowOFDMSymbolDiffMagPhase(resourceGrid,s1,s2):
    #num_subcarriers, num_ofdm_symbols = resourceGrid.shape
    num_symbols, num_subcarriers  = resourceGrid.shape
    colors = plt.cm.jet(np.linspace(0, 1, num_symbols))  # Create a color map
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 8))  # Create a 2x1 subplot

    ofdm_s1 = resourceGrid[s1, :]
    ofdm_s2 = resourceGrid[s2, :]
    ofdm_div = ofdm_s2 / ofdm_s1

    # Aggregate data for easier plotting
    magnitudes = np.abs(ofdm_div)
    phases = np.angle(ofdm_div)
    
    # Plot Magnitudes
    ax[0].plot( magnitudes)
    ax[0].set_title(f'Magnitude of symbol {s2} / symbol {s1}')
    ax[0].set_xlabel('Subcarrier Number')
    ax[0].set_ylabel('Magnitude')
    
    # Plot Phases
    ax[1].plot(phases)
    ax[1].set_title(f'Phase of symbol {s2} / symbol {s1}')
    ax[1].set_xlabel('Subcarrier Number')
    ax[1].set_ylabel('Phase (Radians)')
    
    plt.tight_layout()
    plt.show()



def main():

    with open('lte_20Mhz_rate23.04Mhz_dur_10ms_pci252_traffic/lte_20Mhz_rate23.04Mhz_dur_10ms_pci252_traffic.bin', 'rb') as f:     
        iq_samples = np.fromfile(f, dtype=np.complex64)

    # resample the I/Q data sampled at 23.04 to 30.72
    iq_samples = resample_iq(iq_samples, orig_rate=23.04e6, target_rate=30.72e6)

    sample_rate = 30.72e6
    fft_bin_size = 2048
    NRB = 100
    debug_print = False

    resultsPSS = DetectPSS(iq_samples,fft_bin_size,sample_rate,debug=debug_print)

    print(f'Detected PSS Sequence (N_ID_2): {resultsPSS["max_correlation_index"]}')
    set_gui_parameter('Detected PSS Sequence (N_ID_2)', resultsPSS["max_correlation_index"])
    print(f'Maximum correlation: {resultsPSS["max_correlation"]}')
    set_gui_parameter('Maximum correlation', f'{resultsPSS["max_correlation"]:.6f}')
    print(f'Maximum correlation for PSS0: {resultsPSS["max_correlation_pss0"]}')
    set_gui_parameter('Maximum correlation for PSS0', f'{resultsPSS["max_correlation_pss0"]:.6f}')
    print(f'Maximum correlation for PSS1: {resultsPSS["max_correlation_pss1"]}')
    set_gui_parameter('Maximum correlation for PSS1', f'{resultsPSS["max_correlation_pss1"]:.6f}')
    print(f'Maximum correlation for PSS2: {resultsPSS["max_correlation_pss2"]}')
    set_gui_parameter('Maximum correlation for PSS2', f'{resultsPSS["max_correlation_pss2"]:.6f}')
    print(f'Position of maximum correlation: {resultsPSS["max_correlation_position"]}')
    set_gui_parameter('Position of maximum correlation', resultsPSS["max_correlation_position"])
    print(f'Estimated Frequency Offset: {resultsPSS["frequency_offset"]} Hz')
    set_gui_parameter('Estimated Frequency Offset', f'{resultsPSS["frequency_offset"]:.2f} Hz')

    max_correlation_index = resultsPSS["max_correlation_index"]
    pss_start = resultsPSS["pss_start"]
    pss_time_domain = resultsPSS["pss_time_domain"]
    ofdm_symbols = resultsPSS["ofdm_symbols"]
    detected_pss_freq_domain = resultsPSS["max_window_samples"]
    frequency_offset = resultsPSS["frequency_offset"]

    resourceGrid = getResourceGrid(ofdm_symbols, nRB = NRB, removeDC = True) 
    print("Dimension of resourceGrid = ",resourceGrid.shape)
    set_gui_parameter('Dimension of resourceGrid', f'{resourceGrid.shape}')

    # Detect SSS
    N_ID_2 = max_correlation_index 
    resultsSSS = DetectSSS(resourceGrid, N_ID_2, frequency_offset, nRB = NRB, samplingRate = sample_rate, debug = debug_print )

    N_ID_1 = resultsSSS["N_ID_1"]
    sss_no_correction = resultsSSS["sss_no_correction"]
    sss_corrected = resultsSSS["sss_corrected"]
    detected_subframe = resultsSSS["detected_subframe"]

    print('Detected Subframe : ', detected_subframe)
    set_gui_parameter('Detected Subframe', detected_subframe)

    print('Detected N_ID_2 (PSS) : ', N_ID_2)
    set_gui_parameter('Detected N_ID_2 (PSS)', N_ID_2)
    print('Detected N_ID_1 (SSS) : ', N_ID_1)
    set_gui_parameter('Detected N_ID_1 (SSS)', N_ID_1)

    PCI = getPCI(N_ID_1, N_ID_2)
    print('Detected PCI: ', PCI)
    set_gui_parameter('Detected PCI', PCI)

    ShowPSS(iq_samples, detected_pss_freq_domain, max_correlation_index, ofdm_symbols, pss_start, pss_time_domain)
    ShowGrid(ofdm_symbols, nRB = NRB, zmin = -25, zmax = 0) 
    #ShowGridIQ(ofdm_symbols, nRB = NRB) 
    ShowSSS(sss_no_correction, sss_corrected, N_ID_1, N_ID_2,detected_subframe)  

    # calculate the channel coefficient corresponding to each CRS and return the recieved CRS (crs_rx), channel coefficient (h) and 
    # the list of subcarrier number for crs (crs_k). All of these crs_rx, h, crs_k would carry the data for symbol 0,4,7,11 of the 
    # subframe in resourceGrid 
    # crs_rx, h, crs_k = GetCRSandChannelCoef(resourceGrid,PCI,nRB = 100, method = "generate", debug=True) 
    crs_rx, crs_ex, h, crs_k = GetCRSandChannelCoef(resourceGrid,PCI,nRB = 100, method = "generate", subframe=0, debug=False) 
    #crs_rx, crs_ex, h, crs_k = GetCRSandChannelCoef(resourceGrid,PCI,nRB = 100, method = "testvector", subframe=0) 

    # show constellation of crs_rx(recieved crs),crs_ex(expected crs) and h (=crx_rx/crx_ex)
    ShowCRS(crs_rx, crs_ex, h)

    # create an empty resource grid and put the h (channel coefficient) values at the poisition of each CRS RE
    hResourceGrid = cloneArray(resourceGrid, 0.0+1j*0.0)   # create an resource grid, the dimension of which is copied from resourceGrid
    #hResourceGrid = hResourceGrid.astype(complex)
    hResourceGrid = setResourceGrid(hResourceGrid, symb=0, k_list=crs_k[0], v_list=h[0])
    hResourceGrid = setResourceGrid(hResourceGrid, symb=4, k_list=crs_k[1], v_list=h[1])
    hResourceGrid = setResourceGrid(hResourceGrid, symb=7, k_list=crs_k[2], v_list=h[2])
    hResourceGrid = setResourceGrid(hResourceGrid, symb=11, k_list=crs_k[3], v_list=h[3])
    print("len of k_list = ", len(crs_k[0])) # print the length of crs symbols. just for troubleshooting
    plotGridImage(hResourceGrid)

    # mode 0 : interpolate in both time and frequency, mode 1 for frequency domain only, 2 for time only, 3 for no interpolation
    #hResourceGrid_interpolated = interpolateGrid(hResourceGrid, mode = 0, td_method = "copy")
    hResourceGrid_interpolated = interpolateGrid(hResourceGrid, mode = 0, td_method = "interpolate", direction="ccw")

    # plot resourceGrid (2D grid)
    plotGridImage(hResourceGrid_interpolated)

    # plot I/Q constellation of all 14 OFDM symbols within the specified resource Grid
    ShowResourceGridIQ(hResourceGrid_interpolated, figTitle="Interpolated [h] Grid I/Q", figTitleColor="green")

    # plot line graph for each OFDM symbols within the specified resource grid
    ShowResourceGridMagPhase(hResourceGrid_interpolated)

    # correct/compensate the resourceGrid with hResourceGrid_interpolated
    resourceGrid_corrected = ResourceGridDiv(resourceGrid, hResourceGrid_interpolated)

    # Check for NaN or Inf values
    if np.any(np.isnan(resourceGrid_corrected)) or np.any(np.isinf(resourceGrid_corrected)):
        print("Data contains NaN or infinite values!")
        resourceGrid_corrected = np.clip(resourceGrid_corrected, -20, 20)

    # Plot I/Q for 14 OFDM symbols of original resource grid (i.e, unequalized resource grid)
    ShowResourceGridIQ(resourceGrid, clip = 20, figTitle="Recieved Resource Grid I/Q : Before Equalization", figTitleColor="green")

    # Plot I/Q for 14 OFDM symbols of the resource grid after equalization
    ShowResourceGridIQ(resourceGrid_corrected, clip = 10, figTitle="Corrected Resource Grid I/Q : After Equalization", figTitleColor="green")
    #ShowResourceGridIQ(resourceGrid_corrected, clip = 10, figTitle="Corrected Resource Grid I/Q", figTitleColor="green", data_range = [0,12*1])

if __name__ == "__main__":
    main()    