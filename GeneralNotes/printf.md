# printf notes

## Category
Notes

## Points
N/A

## Description
This note gives some details of the `printf` format specifier exploit

## Keywords
printf, C, pwntools 

## Notes
In certain circumstances, the C language's workhorse console display function, `printf()` can be exploited to read or write to memory.

* [printf normal usage](#printf-normal-usage)
* [printf vulnerable usage](#printf-vulnerable-usage)
* [Reading through the stack](#reading-through-the-stack)
* [Writing to memory](#writing-to-memory)

### printf normal usage
`printf` is a function included in the `stdio.h` header for displaying text on the console. It can display various combinations of a string literal, specified in the first argument to `printf`, and variables, specified in subsequent arguments. To specify where the variables should be displayed within the string literal, we use **format specifiers**. These start with a `%`, and are followed by a letter denoting the type we are expecting (e.g. `d` for signed decimal integer, and `s` for string).

I won't cover all the possible format specifiers in this note - there are plenty of places to find that information with a quick Google - but the one's we will use will be:

| Specifier | Description
| ------    | ------
| %c | Display an argument as a char
| %d | Display an argument signed decimal integer
| %x | Display an argument as an unsigned hexadecimal integer
| %p | Display an argument as a pointer
| %s | Display an argument as a string
| %n | Displays nothing, but is passed a pointer argument - a pointer to a signed int - and sets that signed int to the number of characters printed out so far.

A simple example of some code using `printf` is below:
```c
#include<stdio.h>

int main()
{
  int i = 10;
  char s[] = "Fred";

  // Print a string literal
  printf("Hello, world!\n");

  // Print a string variable within a literal
  printf("Hi, %s\n", s);

  // Print a string variable and an integer within a literal
  printf("%s's age is %d\n", s, i);

  return 0;
}
```

Compiling and running this code, we get:
```
$ gcc hello-world.c -o hello-world
$ ./hello-world 
Hello, world!
Hi, Fred
Fred's age is 10
```

However, `printf` doesn't care whether the types of variables match the format specifiers. We can mess with it quite easily:
```c
#include<stdio.h>

int main()
{
  int i = 10;
  char s[] = "Fred";

  // Print a string literal
  printf("Hello, world!\n");

  // Print a signed integer, but pass a string
  printf("Hi, %d\n", s);

  // Print a hexidecimal int, passing a string, and a pointer passing an int
  printf("%x's age is %p\n", s, i);

  return 0;
}
```

Compiling and running we now get:
```
$ gcc mismatch.c -o mismatch
$ ./mismatch 
Hello, world!
Hi, 1871460560
6f8c38d0's age is 0xa
```

> It should be pointed out that if you build using `gcc` with `-Wall`, it does warn you about the `printf` mismatches:
```
$ gcc mismatch.c -o mismatch -Wall
mismatch.c: In function ‘main’:
mismatch.c:12:16: warning: format ‘%d’ expects argument of type ‘int’, but argument 2 has type ‘char *’ [-Wformat=]
   12 |   printf("Hi, %d\n", s);
      |               ~^     ~
      |                |     |
      |                int   char *
      |               %s
mismatch.c:15:12: warning: format ‘%x’ expects argument of type ‘unsigned int’, but argument 2 has type ‘char *’ [-Wformat=]
   15 |   printf("%x's age is %p\n", s, i);
      |           ~^                 ~
      |            |                 |
      |            unsigned int      char *
      |           %s
mismatch.c:15:24: warning: format ‘%p’ expects argument of type ‘void *’, but argument 3 has type ‘int’ [-Wformat=]
   15 |   printf("%x's age is %p\n", s, i);
      |                       ~^        ~
      |                        |        |
      |                        void *   int
      |                       %d
```
> This is true of things we'll do in the rest of this note, but for brevity, we'll always build with only basic warnings on.

Finally, in normal operation of `printf`, we don't have to use the parameters in the order in which they are specified. This feature of `printf` isn't always mentioned in `printf` descriptions, but it's very useful to us.

By inserting `n$` between the `%` and the format letter (where n is an integer between 1 and the number of arguments), we can specify which of the arguments we want to apply to this format specifier. An example will help explain:
```c
#include<stdio.h>

int main()
{
  int i = 20;
  int j = 10;
  int k = 5;
  char c = 'A';

  // Normal use - you can't mix positional and non-positional
  // We can repeatedly use an argument
  printf("%1$d, %4$c, %2$d, %4$c, %3$d, %4$c\n", i, j, k, c);


  // We can skip the first argument
  // What happens with the subsequent specifiers
  // is compiler/platform dependent.
  printf("%2$d %d %c\n", i, j, k, c);

  return 0;
}
```

When compiled and run, we can see how the positional arguments work:
```
$ gcc argument-select.c -o argument-select
$ ./argument-select 
20, A, 10, A, 5, A
10 5 A
```
> This output is from Clang (aliased as gcc) on MacOS X. Using gcc on Linux, the output is:
> 20, A, 10, A, 5, A
> 10 20
>
> where the arguments reset and start from the beginning, showing argument 1, 2 as integers, and then
> 3 as a character (as the value is 10, it just shows a line feed).

So how can we exploit `printf`?

### printf vulnerable usage
What happens if we use `printf` with format specifiers, but we don't specify any arguments? Let's try:
```c
#include <stdio.h>

int main()
{
  printf("%d\n%d\n%d\n");

  return 0;
}
```
We still get some output:
```
$ gcc no-args.c -o no-args
$ ./no-args 
-2060149592
-2060149576
-1444055272
```
We still get some output. So where are those values coming from?

Let's print more (and as hex) and see if we can work it out:
```c
#include <stdio.h>
#include <string.h>

int main()
{
  // Some variables - unused, but show up later
  char s[] = "AAAAAAAAAAAA";
  int a = 1;
  int b = 2;
  int c = 3;

  // Holds are printf format strings so we can
  // build them in a loop.
  char x[15];

  for (unsigned int i=1; i<20; ++i)
  {
    // Create our format strings for %x
    sprintf(x, "%1$d \t %%%1$d$x\n", i);

    // Show us what happens with no arguments
    printf(x);
  }

  return 0;
}
```
This prints out the offset parameter number followed by the contents at that parameter, interpreted as a hexadecimal integer:
```
$ gcc -m32 no-args-x.c -o no-args-x
$ ./no-args-x 
1 	 5660e008
2 	 2
3 	 5660d1c0
4 	 0
5 	 0
6 	 5660c034
7 	 37f62a28
8 	 25200920
9 	 a782439
10 	 a78
11 	 f7db3c1e
12 	 41f613fc
13 	 41414141
14 	 41414141
15 	 414141
16 	 3
17 	 2
18 	 1
19 	 13
```
Now we can start to see what we're looking at. The first byte of offset 12, and all of offsets 13, 14 and 15 contain 12 ASCII values for the letter 'A'. Offset 16 has the value 3 in it, 17 has 2, and 18 has 1. These are the variables from our code! Our `s`, `a`, `b` and `c`. These are values off the stack!

We build this executable as 32-bit so it shows things a bit more clearly than a 64-bit executable. Below is the output from a 32-bit and 64-bit executables showing hexadecimal integers (%x) and pointers (%p) to clarify. It shows the relevant offsets only, which have shifted from above with the addition of more local variables to handle the %p output, and change between the 64-bit and 32-bit executables:

|            | 32-bit |         |            | 64-bit |        |
| :-------:  | ------ | ------- | -----      | ------ | ------ |
| **Offset** | **%x** | **%p**  | **Offset** | **%x** | **%p** |
| 13 | 33312520 | 0x33312520 | 13 | 0        | (nil)              |
| 14 | a7824    | 0xa7824    | 14 | 41c631f0 | 0x4141414141c631f0 |
| 15 | f7d7ac1e | 0xf7d7ac1e | 15 | 41414141 | 0x41414141414141   |
| 16 | 41f283fc | 0x41f283fc | 16 | 3        | 0x200000003        |
| 17 | 41414141 | 0x41414141 | 17 | 1        | 0x1100000001       |
| 18 | 41414141 | 0x41414141 | 18 | f3c631f0 | 0x561ef3c631f0     |
| 19 | 414141   | 0x414141   | 19 | 8131bd0a | 0x7ff58131bd0a     |
| 20 | 3        | 0x3        | 20 | 72064298 | 0x7ffd72064298     |
| 21 | 2        | 0x2        | 21 | 0        | 0x100000000        |
| 22 | 1        | 0x1        | 22 | f3c63145 | 0x561ef3c63145     |
| 23 | 17       | 0x17       | 23 | 8131b7cf | 0x7ff58131b7cf     |


### Reading through the stack

### Writing to memory


