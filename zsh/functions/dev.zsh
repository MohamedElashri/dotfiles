# General development helpers.

crun() {
  mkdir -p "build" && g++ "$1.cpp" -std=c++17 -o "build/$1.out" && "./build/$1.out"
}

GrePFind() {
  grep -rnw "$1" -e "$2"
}
