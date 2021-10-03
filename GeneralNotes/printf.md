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
mismatch.c:12:22: warning: format specifies type 'int' but the argument has type 'char *' [-Wformat]
  printf("Hi, %d\n", s);
              ~~     ^
              %s
mismatch.c:15:30: warning: format specifies type 'unsigned int' but the argument has type 'char *' [-Wformat]
  printf("%x's age is %p\n", s, i);
          ~~                 ^
          %s
mismatch.c:15:33: warning: format specifies type 'void *' but the argument has type 'int' [-Wformat]
  printf("%x's age is %p\n", s, i);
                      ~~        ^
                      %d
3 warnings generated.
$ ./mismatch 
Hello, world!
Hi, 1871460560
6f8c38d0's age is 0xa
```
> *Note*: We do get warnings from the compiler that we have incorrectly matched format specifiers to variable types, but `printf` doesn't care, and we can still run this code.

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

  // Normal use - you can't mis positional and non-positional
  // We can repeatedly use an argument
  printf("%1$d, %4$c, %2$d, %4$c, %3$d, %4$c\n", i, j, k, c);


  // We can skip the first argument
  // Arguments will continue to be grabbed from
  // after the specified argunent
  // We'll get a warning about mixing positional and non-positional,
  // but it's useful knowledge
  printf("%2$d %d %c\n", i, j, k, c);

  return 0;
}
```

When compiled and run, we can see how the positional arguments work:
```
$ gcc argument-select.c -o argument-select
argument-select.c:20:17: warning: cannot mix positional and non-positional arguments in format string [-Wformat]
  printf("%2$d %d %c\n", i, j, k, c);
               ~^
1 warning generated.
$ ./argument-select 
20, A, 10, A, 5, A
10 5 A
```

We get the warning about mixing positional and non-positional arguments, but it still works!

So how can we exploit this?

### printf vulnerable usage
What happens if we use `printf` with format specifiers, but we don't specify any arguments?

### Reading through the stack

### Writing to memory


