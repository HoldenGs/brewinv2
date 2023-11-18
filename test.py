
from interpreterv2 import Interpreter     # imports interpreter

def main():
	# all programs will be provided to your interpreter as a python string, 
	# just as shown here.
	program_source = """
func main() {
    
    print(catalan(5));
	
}

func catalan(n)
{
    if (n <= 1)
    {
        return 1;
    }
    
    i = 0;
    res = 0;
    while (i < n)
    {
        tmp = catalan(i);
        res = res + tmp;
        i = i + 1;
    }
    
    return res;
    
}

	"""
	
	interp = Interpreter(trace_output=False)
	interp.run(program_source)
 
if __name__ == "__main__":
	main()