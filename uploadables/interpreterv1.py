from brewparse import parse_program
from intbase import InterpreterBase
from element import Element
from intbase import ErrorType


class Interpreter(InterpreterBase):
	ast = None
	variables = {}
	functions = {}
	frames = []

	def __init__(self, console_output=True, inp=None, trace_output=False):
		super().__init__(console_output, inp)
		self.trace_output = trace_output

	# Run program
	def run(self, program):
		self.ast = parse_program(program)
  
		if self.ast.get("functions") == None:
			super().error(ErrorType.FAULT_ERROR, "No functions found")

		self.functions = self.ast.get("functions")
		if self.trace_output:
			print("Functions:")
			for func in self.functions:
				print(func)
  
		for func in self.functions:
			if func.get("name") == "main":
				return self.run_function(func, [])

		super().error(ErrorType.NAME_ERROR, "No main function found")

	def run_function(self, func_node, args):
		self.frames.append({func_node.get("name"): args})
		for statement_node in func_node.get("statements"):
			self.run_statement(statement_node)

	def run_statement(self, statement_node):
		if statement_node.elem_type == "=":
			self.do_assignment(statement_node)
		elif statement_node.elem_type == InterpreterBase.FCALL_DEF:
			return self.do_function_call(statement_node)
		#else:
			#super().error(ErrorType.TYPE_ERROR, "Unknown statement type: {}".format(statement_node.elem_type))

	def do_assignment(self, statement_node):
		var_name = statement_node.get("name")
		# if not var_name[0].isalpha() and var_name[0] != "_" or not all(c.isalnum() or c == "_" for c in var_name):
		# 	super().error(ErrorType.NAME_ERROR, f"Invalid variable name: {var_name}")
		if self.trace_output:
			print("Assigning statement to variable: {} = {}".format(var_name, statement_node.get("expression")))
		val = self.evaluate_expression(statement_node.get("expression"))
		if val is None:
			self.variables[var_name] = Element(InterpreterBase.STRING_DEF, val=val)
		else:
			self.variables[var_name] = val

	def evaluate_expression(self, expression_node):
		if self.trace_output:
			print("Evaluating expression: {}".format(expression_node))
   
		if expression_node.elem_type in [InterpreterBase.INT_DEF, InterpreterBase.STRING_DEF]:
			return expression_node
		elif expression_node.elem_type in ["+", "-"]:
			return self.binary_operation(expression_node)
		elif expression_node.elem_type == "var":
			var_name = expression_node.get("name")
			if var_name not in self.variables:
				super().error(ErrorType.NAME_ERROR, f"Variable {var_name} has not been defined")
			return self.evaluate_expression(self.variables[var_name])
		elif expression_node.elem_type == "fcall":
			# if expression_node.get("name") != "inputi":
			# 	super().error(ErrorType.NAME_ERROR, f"Only inputi() function calls are supported within expressions")
			return self.do_function_call(expression_node)
		else:
			return None
			#super().error(ErrorType.TYPE_ERROR, "Unknown expression type: {}".format(expression_node.elem_type))

	def binary_operation(self, expression_node):
		op1 = self.evaluate_expression(expression_node.get("op1"))
		op2 = self.evaluate_expression(expression_node.get("op2"))
   
		if op1.elem_type != op2.elem_type:
			super().error(ErrorType.TYPE_ERROR, "Type mismatch on binary operation between {} and {}: {} {} {}".format(op1.elem_type, op2.elem_type, op1.get("val"), expression_node.elem_type, op2.get("val")))
   
		if op1.elem_type == "int":
			match expression_node.elem_type:
				case "+":
					sum = op1.get("val") + op2.get("val")
					return Element(InterpreterBase.INT_DEF, val=sum)
				case "-":
					difference = op1.get("val") - op2.get("val")
					return Element(InterpreterBase.INT_DEF, val=difference)

		if op1.elem_type == "string":
			match expression_node.elem_type:
				case "+":
					concat = op1.get("val") + op2.get("val")
					return Element(InterpreterBase.STRING_DEF, val=concat)
				case "-":
					super().error(ErrorType.TYPE_ERROR, "Cannot subtract strings: {} - {}".format(op1.get("val"), op2.get("val")))

	def do_function_call(self, statement_node):
		fname = statement_node.get("name")
		args = statement_node.get("args")
  
		if self.trace_output:
			print("Calling function: {}".format(fname))
			print("Args: {}".format(args))
   
		if fname == "print":
			self.print(args)
			return
		if fname == "inputi":
			if len(args) > 1:
				super().error(ErrorType.NAME_ERROR, f"No inputi() function found that takes > 1 parameter")
			elif len(args) == 1:
				super().output(self.evaluate_expression(args[0]).get("val"))
    
			return Element(InterpreterBase.INT_DEF, val=self.inputi(args))

		# for func in self.functions:
		# 	if func.get("name") == fname:
		# 		return self.run_function(func, args)
  
		super().error(ErrorType.NAME_ERROR, "Unknown function: {}".format(fname))
  
	def inputi(self, args):
		return int(super().get_input())

	def print(self, args):
		eval_args = [self.evaluate_expression(arg) for arg in args]
		string_args = [str(arg.get("val")) for arg in eval_args]
		super().output(''.join(string_args))