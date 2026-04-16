/*
 *  Copyright (c) 2003-2010, Mark Borgerding. All rights reserved.
 *  This file is part of KISS FFT - https://github.com/mborgerding/kissfft
 *
 *  SPDX-License-Identifier: BSD-3-Clause
 *  See COPYING file for more information.
 */

#ifndef KISS_FFT_GUTS_H
#define KISS_FFT_GUTS_H

#define MAXFACTORS 32

struct kiss_fft_state{
    int nfft;
    int inverse;
    int factors[2*MAXFACTORS];
    kiss_fft_cpx twiddles[1];
};

#define pcpx(c) \
    fprintf(stderr,"%g + %gi\n",(double)((c)->r),(double)((c)->i))

#ifdef FIXED_POINT
#   error "Fixed point not supported in this simplified guts"
#else
#   define kiss_fft_scalar float
#   define C_MUL(m,a,b) \
    do{ (m).r = (a).r*(b).r - (a).i*(b).i;\
        (m).i = (a).r*(b).i + (a).i*(b).r; }while(0)
#   define C_FIXDIV(c,div) /* no-op */
#   define C_SUB( res, a,b)\
    do { (res).r=(a).r-(b).r;  (res).i=(a).i-(b).i; }while(0)
#   define C_ADD( res, a,b)\
    do { (res).r=(a).r+(b).r;  (res).i=(a).i+(b).i; }while(0)
#   define C_ADDTO( res , a)\
    do { (res).r += (a).r;  (res).i += (a).i; }while(0)
#   define C_SUBFROM( res , a)\
    do { (res).r -= (a).r;  (res).i -= (a).i; }while(0)
#   define C_MULBYSCALAR( c, s ) \
    do{ (c).r *= (s); (c).i *= (s); }while(0)
#   define kf_cexp(x,phase) \
    do{ \
        (x)->r = cos(phase);\
        (x)->i = sin(phase);\
    }while(0)
#endif

#define KISS_FFT_TMP_ALLOC(nbytes) malloc(nbytes)
#define KISS_FFT_TMP_FREE(ptr) free(ptr)
#define KISS_FFT_ERROR(msg) fprintf(stderr, "kissfft error: %s\n", msg)

#endif
