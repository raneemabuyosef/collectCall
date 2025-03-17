#include <stdio.h>
#include<barvinok/barvinok.h>
#include<gmp.h>
#include<isl/set.h>
#include<isl/map.h>
#include <isl/ctx.h>
#include <barvinok/isl.h>
#include<isl/polynomial.h>
int main(){
/*
  const char *constraint_string = "[n] -> { [i] : 0 <= i < 8*n  and i = n and n > 10 }";
    isl_set *set = isl_set_read_from_str(ctx, constraint_string);
   FILE *input = fopen("./isl_dump.txt", "r");
    // Print the set
//    printf("ISL Set:\n");
// isl_set_dump(set);
  //  printf("\n");
    
//   isl_pw_qpolynomial *cardinality = isl_set_card(set); 
  //  isl_pw_qpolynomial_dump(cardinality);
    // Free resources
//    isl_set_free(set);
  // isl_ctx_free(ctx);
*/
    
    isl_ctx *ctx = isl_ctx_alloc();	
    FILE *input = fopen("./isl_dump.txt", "r");
//    constraint_string = "[n] -> {[i0,i1] -> [j0,j1] : i0 = j0 and 0 <= i0 < n  and 0 < j0 < 19 and 0 < j1 < 19 and 0 < i1 < n}";
    isl_basic_map *map = isl_basic_map_read_from_file(ctx, input);
    isl_pw_qpolynomial *cardinality = isl_basic_map_card(map);
    FILE *output = fopen("isl_card.txt", "w");
    isl_pw_qpolynomial_print(cardinality, output,0);
    fclose(output);



	return 0;}
