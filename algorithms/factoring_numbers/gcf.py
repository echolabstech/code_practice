def generalizedGCD(num_pos_ints, some_integers):
    gcf_factors = {}
    for integer in some_integers:
        factors = range(1, integer+1)
        for factor in factors:
            if integer % factor == 0:
                if factor in gcf_factors:
                    gcf_factors[factor] += 1
                else:
                    gcf_factors[factor] = 1
    gcf = 1
    for key in gcf_factors:
        if (gcf_factors[key] >= gcf_factors[gcf]):
            gcf = key