// clang -O3 -flto --target=wasm32 -mbulk-memory --no-standard-libraries -Wl,--export-all -Wl,--no-entry -Wl,--lto-O3 -o cdb_djp_hash.wasm cdb_djp_hash.c
// wasm-objdump -x cdb_djp_hash.wasm 

// __attribute__((import_module("imports"), import_name("logi"))) void logi(int);
// __attribute__((import_module("imports"), import_name("logf"))) void logf(float);

extern unsigned char __heap_base;

#define CDB_HASHSTART 5381

typedef unsigned int uint32;

uint32 cdb_djp_hashadd(uint32 h,unsigned char c)
{
  h += (h << 5);
  return h ^ c;
}

uint32 cdb_djp_hash(unsigned char *buf,unsigned int len)
{
  uint32 h;

  h = CDB_HASHSTART;
  while (len) {
    h = cdb_djp_hashadd(h,*buf++);
    --len;
  }
  return h;
}

