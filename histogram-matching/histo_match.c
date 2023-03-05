// clang -O3 -flto --target=wasm32 -mbulk-memory --no-standard-libraries -Wl,--export-all -Wl,--no-entry -Wl,--lto-O3 -Wl,-z,stack-size=$[40 * 1024] -o histo_match.wasm histo_match.c
// wasm-objdump -x histo_match.wasm 
// __attribute__((import_module("imports"), import_name("logi"))) void logi(int);
// __attribute__((import_module("imports"), import_name("logf"))) void logf(float);

extern unsigned char __heap_base;
/*
unsigned int bump_pointer = &__heap_base;
void* malloc(int n) {
  unsigned int r = bump_pointer;
  bump_pointer += n;
  return (void *)r;
}

void free(void* p) {
  // lol
}
*/

int memory_grow(int delta) {
    return __builtin_wasm_memory_grow(0, delta);
}

void make_cdf(int size, unsigned char *img, float **cdf) {
    int i,j;
    int sum = (float)(size/4);
    for(i=0;i<size;++i) {
        j=i%4;
        if (j==3) continue;
        cdf[j][img[i]]+=(float)1.0;
    }
    for(j=0;j<3;++j) {
        cdf[j][0]/=sum;
        for(i=1;i<256;++i) {
            cdf[j][i]/=sum;
            cdf[j][i]+=cdf[j][i-1];
        }
    }
}

void histo_match(int size_ref, unsigned char *img_ref, int size, unsigned char *img_src, unsigned char *img_dst) {
    // size = w*h*4
    int i,j,k;
    float cdf_refp[3*256];
    float *cdf_ref[3]={&cdf_refp[0], &cdf_refp[256], &cdf_refp[2*256]};
    float cdf_srcp[3*256];
    float *cdf_src[3]={&cdf_srcp[0], &cdf_srcp[256], &cdf_srcp[2*256]};
    unsigned char mapp[3*256];
    unsigned char *map[3]={&mapp[0], &mapp[256], &mapp[2*256]};
    
    float f;
    for(j=0;j<3;++j) {
        for(i=0;i<256;++i) {
            cdf_ref[j][i]=0.0;
            cdf_src[j][i]=0.0;
        }
    }
    make_cdf(size_ref, img_ref, cdf_ref);
    make_cdf(size, img_src, cdf_src);

    for(j=0;j<3;++j) {
        f=cdf_src[j][0];
        k=0; // k is in ref space
        // i is in src space
        for(i=0;i<256;++i) {
            f=cdf_src[j][i];
            while (cdf_ref[j][k]<f && k<255) {
                ++k;
            }
            map[j][i]=k;
        }
    }
    for(i=0;i<size;++i) {
        j=i%4;
        if (j==3) {
            img_dst[i] = 255;
            continue;
        }
        img_dst[i] = map[j][img_src[i]];
    }
    // logi(size);
}
