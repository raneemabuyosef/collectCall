#include <stdio.h>
#include<barvinok/barvinok.h>
#include<gmp.h>
#include<isl/set.h>
#include<isl/map.h>
#include <isl/ctx.h>
#include <barvinok/isl.h>
#include<isl/polynomial.h>
int main(){

    isl_ctx *ctx = isl_ctx_alloc();
    FILE *input = fopen("./isl_set_dump.txt", "r");
    isl_set *set = isl_set_read_from_file(ctx, input); 
   isl_pw_qpolynomial *cardinality = isl_set_card(set);  
    FILE *output = fopen("isl_set_card.txt", "w");
    isl_pw_qpolynomial_print(cardinality, output,0);
    fclose(output);



	return 0;}
