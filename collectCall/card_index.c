#include <stdio.h>
#include<barvinok/barvinok.h>
#include<gmp.h>
#include<isl/set.h>
#include<isl/map.h>
#include <isl/ctx.h>
#include <barvinok/isl.h>
#include<isl/polynomial.h>
#include <isl/ctx.h>
#include <isl/set.h>
#include <isl/printer.h>

int main(int argc, char *argv[]) {
    // Initialize the ISL context
    isl_ctx *ctx = isl_ctx_alloc();
    
    if (!ctx) {
        fprintf(stderr, "Error: Unable to allocate ISL context\n");
        return -1;
    }

    FILE *input = fopen("./isl_index_dump.txt", "r");

    isl_set *set = isl_set_read_from_file(ctx, input);
    fclose(input);
    

    isl_set *projected_set = isl_set_project_out(set, isl_dim_set, atoi(argv[1]),  1);

    //    isl_printer *print = isl_printer_to_file(ctx, stdout);
  //  isl_printer_print_set(print, projected_set);
    //isl_printer_free(print);	
    
    isl_pw_qpolynomial *projected_cardinality = isl_set_card(projected_set);
    if (!projected_cardinality) {
        fprintf(stderr, "Error computing projected cardinality\n");
        isl_set_free(projected_set);
        return -1;
    }

    // Open the output file
    FILE *output = fopen("isl_index_card.txt", "w");
    if (!output) {
        perror("Error opening output file");
        isl_pw_qpolynomial_free(projected_cardinality);
        isl_set_free(projected_set);
        return -1;
    }

    // Print the cardinality to the output file
    isl_printer *printer = isl_printer_to_file(ctx, output);
    isl_printer_print_pw_qpolynomial(printer, projected_cardinality);

    // Cleanup
    fclose(output);
    //isl_printer_free(printer);
   // isl_pw_qpolynomial_free(projected_cardinality);
   // isl_set_free(projected_set);

    return 0;
}

