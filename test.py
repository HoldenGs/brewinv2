
from interpreterv2 import Interpreter     # imports interpreter

def main():
	# all programs will be provided to your interpreter as a python string, 
	# just as shown here.
	program_source = """
func main() {
 print(fib(5));
}

func fib(n) {
 if (n < 3) {
  return 1;
 } else {
  return fib(n-2) + fib(n-1);
 }
}
	"""
	
	interp = Interpreter(trace_output=False)
	interp.run(program_source)
 
if __name__ == "__main__":
	main()