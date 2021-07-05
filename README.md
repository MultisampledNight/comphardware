# comphardware

Compare hardware like two numbers.

## Please notice

The library probably isn't suitable for production use yet. Reasons include:

- No AMD processor support, if the user has an AMD CPU or the game lists one as
  requirement, this library will just return `None` or a highly unsuitable CPU
  for them.
- No real testing done yet.
- Depending on having freeglut installed for getting the user's GPU.

If I/we somehow manage to fix all of these points, I might consider going
stable. 

## Reason

The initial factor was the upcoming shop in
[Rare](https://github.com/Dummerle/Rare). Dummerle recently added the hardware
requirements, which caused me to think: Who are these hardware requirements
actually made for? The end user? Do they even know about their hardware?
Wouldn't it be way easier to let the program say if the game the user currently
looks at isn't even runnable on their PC, before they buy it and it's too late?

## Installation

Firstly, install [freeglut](http://freeglut.sourceforge.net/index.php#download)
and get it somehow on your PATH. This is required for getting the GPU. On Arch
Linux this should be as simple as

```
sudo pacman -S freeglut
```

Then, to install this library:

```python
python3 -m pip install comphardware
```
should suffice, or if you want to browse through the code
```
git clone https://github.com/MultisampledNight/comphardware
cd comphardware
```

## Usage

Here's an interactive prompt on how comphardware can be used, in this case, for
comparing the minimum requirements of Satisfactory to the user's hardware
```python
In [1]: import comphardware

In [2]: user_setup = comphardware.user_setup()

In [3]: # let's just imagine that this response comes from an API

In [4]: api_response = {
   ...:     "Processor": "i5-3570k 3.4 GHz 4 Core (64-Bit)",
   ...:     "Memory": "8 GB RAM",
   ...:     "Graphics": "GTX 760 2GB",
   ...: }

In [5]: satisfactory_min_setup = comphardware.setup_from_clutter(
   ...:     api_response["Processor"],
   ...:     api_response["Graphics"],
   ...:     api_response["Memory"],
   ...: )

In [6]: # can the PC of the user handle Satisfactory?

In [7]: user_setup > satisfactory_min_setup
Out[7]: False

In [8]: # no :(

In [9]: user_setup.gpu > satisfactory_min_setup.gpu
Out[9]: True

In [10]: user_setup.cpu > satisfactory_min_setup.cpu
Out[10]: False

In [11]: user_setup.ram > satisfactory_min_setup.ram
Out[11]: False

In [12]: # the GPU would actually be okay, but CPU and RAM aren't powerful enough

In [13]: user_setup.cpu
Out[13]:
	CPU(
		model = "i5-2520M",
		vendor = "intel",
		corecount = 2,
		clockspeed = 2500.0 MHz,
		score = 36.08490566037736
	)

In [14]: # hehe, well, okay, an i5-2520M might be really not as good as an i5-3570K
```

## Documentation

There is no real one, the library is way too small for that.
`help("comphardware")` in the Python REPL is quite explanatory though

## Credits

Credits go to

- Wikipedia for the GPU information
- [Dummerle](https://github.com/Dummerle) &
  [loathingKernel](https://github.com/loathingKernel) for some thoughts and code
  on getting the user's CPU and GPU
- [This code which parses the Intel ARK in PHP](https://github.com/divinity76/intel-cpu-database)
- You for reading this :D
