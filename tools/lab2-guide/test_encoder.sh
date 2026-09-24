#!/usr/bin/env zsh
# Laptop test of the step 2 encoder decoder. Pulls the encoder code out of
# out/stages/animation_step2.c (run `python3 apply.py` first), fakes the two
# switches, and checks the count, with and without contact bounce.
set -e
DIR="${0:A:h}"
F="$DIR/out/stages/animation_step2.c"
[[ -f "$F" ]] || { echo "run: python3 apply.py   (makes $F)"; exit 1; }
TMP=$(mktemp -d)
{
  printf '#include <stdio.h>\n#include <stdint.h>\ntypedef unsigned uint; static uint32_t PINS; static uint32_t gpio_get_all(void){return PINS;}\n'
  sed -n '/^#define ENCODER_A/,/^} ;$/p' "$F"
  sed -n '/^void encoder_callback/,/^}$/p' "$F"
  cat <<'EOF'
static void set(int a,int b){PINS=((uint32_t)a<<ENCODER_A)|((uint32_t)b<<ENCODER_B); encoder_callback(0,0);}
static const int CW[5][2]={{1,1},{0,1},{0,0},{1,0},{1,1}};
static void click(int dir,int rattle){
  for(int k=1;k<5;k++){ int i=dir>0?k:4-k, p=dir>0?k-1:5-k;
    for(int r=0;r<rattle;r++){ set(CW[i][0],CW[i][1]); set(CW[p][0],CW[p][1]); }
    set(CW[i][0],CW[i][1]); } }
static int fails=0;
static void expect(const char*what,int want){ printf("%-26s -> %3d (want %d)%s\n",what,encoder_count,want,encoder_count==want?"":"   FAIL"); if(encoder_count!=want) fails++; }
int main(){
  for(int n=0;n<10;n++) click(+1,0); expect("10 clean CW clicks",10);
  for(int n=0;n<10;n++) click(-1,0); expect("10 clean CCW clicks",0);
  for(int n=0;n<10;n++) click(+1,4); expect("10 CW, 4 rattles per edge",10);
  for(int n=0;n<10;n++) click(-1,4); expect("10 CCW, 4 rattles per edge",0);
  set(0,1); set(0,0); set(0,1); set(1,1); expect("half-click nudge and back",0);
  return fails!=0;
}
EOF
} > "$TMP/enc.c"
cc -w -o "$TMP/enc" "$TMP/enc.c"
"$TMP/enc" && echo "all encoder tests pass"
