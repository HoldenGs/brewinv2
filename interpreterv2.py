from brewparse import parse_program
from intbase import InterpreterBase
from element import Element
from intbase import ErrorType


class Interpreter(InterpreterBase):
	unary_ops = {InterpreterBase.NOT_DEF, InterpreterBase.NEG_DEF}
	binary_ops = {"+", "-", "*", "/", "&&", "||", "==", "!=", "<", ">", "<=", ">="}
	types = {InterpreterBase.INT_DEF, InterpreterBase.STRING_DEF, InterpreterBase.BOOL_DEF, InterpreterBase.NIL_DEF}

	def __init__(self, console_output=True, inp=None, trace_output=False):
		super().__init__(console_output, inp)
		self.trace_output = trace_output
  
	def run(self, program):
		self.ast = parse_program(program)
		self.functions = {}
		self.frames = [{}]
		self.recursion_depth = 0
  
		if self.ast.get("functions") == None:
			super().error(ErrorType.FAULT_ERROR, "No functions found")

		if self.trace_output:
			print("Functions:")
		for func in self.ast.get("functions"):
			
			self.set_function(func)
			if self.trace_output:
				print("{}: {}".format(func.get("name"), func))

		if self.get_function("main", 0) != None:
			if self.trace_output:
				print("Running main entrypoint")
			func = self.get_function("main", 0)
			return self.run_function(func)

		super().error(ErrorType.NAME_ERROR, "No main function found")

	# TODO: Refactor scoping to use a single method call in all the relevant places
	def run_function(self, function_node):
		if self.trace_output:
			print("Running function: {}".format(function_node.get("name")))
   
		f_name = function_node.get("name")
		args = function_node.get("args")

		if f_name == "inputi":
			return self.inputi(args)

		elif f_name == "inputs":
			return self.inputs(args)

		elif f_name == "print":
			self.print(args)
   
		elif self.get_function(f_name, len(args)) != None:
			self.recursion_depth += 1
			
			function_node = self.get_function(f_name, len(args))
			if self.trace_output:
				print("Running function: {}".format(function_node))
    
			self.frames.append({})

			# We don't call the set_variable function here because we don't want to shadow variables
			for i in range(len(args)):
				self.frames[-1][function_node.get("args")[i].get("name")] = self.evaluate_expression(args[i])
			for statement_node in function_node.get("statements"):
				ret = self.run_statement(statement_node)
				if ret != None:
					self.frames.pop()
					return ret
			self.frames.pop()
   
		else:
			super().error(ErrorType.NAME_ERROR, "Unknown Function Referenced: {}, taking {} args".format(f_name, len(args)))
   
	def inputi(self, args):
		if len(args) > 1:
				super().error(ErrorType.NAME_ERROR, f"No inputi() function found that takes > 1 parameter")
		elif len(args) == 1:
			super().output(self.evaluate_expression(args[0]).get("val"))

		return Element(InterpreterBase.INT_DEF, val=int(super().get_input()))

	def inputs(self, args):
		if len(args) > 1:
			super().error(ErrorType.NAME_ERROR, f"No inputs() function found that takes > 1 parameter")
		elif len(args) == 1:
			super().output(self.evaluate_expression(args[0]).get("val"))

		return Element(InterpreterBase.STRING_DEF, val=str(super().get_input()))

	def print(self, args):
		eval_args = [self.evaluate_expression(arg) for arg in args]
		string_args = [str(arg.get("val")) for arg in eval_args]
		string_args = [arg.lower() if arg == "True" or arg == "False" else arg for arg in string_args]
		super().output(''.join(string_args))
  
	def print_frames(self):
		print("Frames:")
		for frame in self.frames:
			print(frame)
			for var in frame:
				print("\t{}: {}".format(var, frame[var]))
    
	def run_statement(self, statement_node):
		if statement_node.elem_type == "=":
			self.run_assignment(statement_node)
		elif statement_node.elem_type == InterpreterBase.FCALL_DEF:
			return self.run_function(statement_node)
		elif statement_node.elem_type == InterpreterBase.RETURN_DEF:
			return self.evaluate_expression(statement_node.get("expression"))
		elif statement_node.elem_type == InterpreterBase.IF_DEF:
			return self.run_if(statement_node)
		elif statement_node.elem_type == InterpreterBase.WHILE_DEF:
			return self.run_while(statement_node)

	def run_while(self, while_node):
		if self.trace_output:
				print("Running while: {}".format(while_node))
		condition = self.evaluate_expression(while_node.get("condition"))
		if condition.elem_type != InterpreterBase.BOOL_DEF:
			super().error(ErrorType.TYPE_ERROR, "Type mismatch on while condition: {}".format(condition.elem_type))
		self.frames.append({})
  
		while self.evaluate_expression(condition).get("val"):
			for statement_node in while_node.get("statements"):
				ret = self.run_statement(statement_node)
				if ret != None:
					self.frames.pop()
					return ret
			condition = self.evaluate_expression(while_node.get("condition"))
		self.frames.pop()
   
	def run_if(self, if_node):
		if self.trace_output:
				print("Running if: {}".format(if_node))
		condition = self.evaluate_expression(if_node.get("condition"))
		if condition.elem_type != InterpreterBase.BOOL_DEF:
			super().error(ErrorType.TYPE_ERROR, "Type mismatch on if condition: {}".format(condition.elem_type))
		self.frames.append({})
  
		if condition.get("val"):
			for statement_node in if_node.get("statements"):
				ret = self.run_statement(statement_node)
				if ret != None:
					self.frames.pop()
					return ret
		elif if_node.get("else_statements") != None:
			for statement_node in if_node.get("else_statements"):
				ret = self.run_statement(statement_node)
				if ret != None:
					self.frames.pop()
					return ret
		self.frames.pop()

	def run_assignment(self, statement_node):
		expression_node = statement_node.get("expression")
		var_name = statement_node.get("name")

		if expression_node.elem_type in self.binary_ops:
			val = self.evaluate_expression(expression_node)
			self.set_variable(var_name, val)
		elif expression_node.elem_type in self.types:
			self.set_variable(var_name, expression_node)
		elif expression_node.elem_type == "fcall":
			self.set_variable(var_name, self.run_function(expression_node))
		elif expression_node.elem_type == "var":
			self.set_variable(var_name, self.evaluate_expression(expression_node))
		else:
			super().error(ErrorType.TYPE_ERROR, f"Invalid assignment: {expression_node.elem_type}")

	def evaluate_expression(self, expression_node):
		match expression_node.elem_type:
			case "fcall":
				return self.run_function(expression_node)
			case "var":
				var = expression_node.get("name")
				return self.evaluate_expression(self.get_variable(var))
			case "int":
				return Element(InterpreterBase.INT_DEF, val=expression_node.get("val"))
			case "string":
				return Element(InterpreterBase.STRING_DEF, val=expression_node.get("val"))
			case "bool":
				return Element(InterpreterBase.BOOL_DEF, val=expression_node.get("val"))
			case "nil":
				return Element(InterpreterBase.NIL_DEF, val=expression_node.get("val"))

		if expression_node.elem_type in self.binary_ops:
			#print("binary op {} between {} and {}".format(expression_node.elem_type, expression_node.get("op1"), expression_node.get("op2")))
			op1 = self.evaluate_expression(expression_node.get("op1"))
			op2 = self.evaluate_expression(expression_node.get("op2"))
			if op1.elem_type != op2.elem_type:
				super().error(ErrorType.TYPE_ERROR, "Type mismatch on binary operation between {} and {}: {} {} {}".format(op1.elem_type, op2.elem_type, op1.get("val"), expression_node.elem_type, op2.get("val")))
			match expression_node.elem_type:
				case "+":
					if op1.elem_type not in [InterpreterBase.INT_DEF, InterpreterBase.STRING_DEF]:
						super().error(ErrorType.TYPE_ERROR, "Unsupported type {} for binary operator '{}'".format(op1.elem_type, expression_node.elem_type))
					sum = op1.get("val") + op2.get("val")
					return Element(op1.elem_type, val=sum)
				case "-":
					diff = op1.get("val") - op2.get("val")
					return Element(InterpreterBase.INT_DEF, val=diff)
				case "*":
					prod = op1.get("val") * op2.get("val")
					return Element(InterpreterBase.INT_DEF, val=prod)
				case "/":
					if op2.get("val") == 0:
						super().error(ErrorType.FAULT_ERROR, "Division by zero")
					quot = op1.get("val") // op2.get("val")
					return Element(InterpreterBase.INT_DEF, val=quot)
				case "&&":
					if op1.elem_type != InterpreterBase.BOOL_DEF or op2.elem_type != InterpreterBase.BOOL_DEF:
						super().error(ErrorType.TYPE_ERROR, "Type mismatch on binary operation between {} and {}: {} {} {}".format(op1.elem_type, op2.elem_type, op1.get("val"), expression_node.elem_type, op2.get("val")))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") and op2.get("val")))
				case "||":
					if op1.elem_type != InterpreterBase.BOOL_DEF or op2.elem_type != InterpreterBase.BOOL_DEF:
						super().error(ErrorType.TYPE_ERROR, "Type mismatch on binary operation between {} and {}: {} {} {}".format(op1.elem_type, op2.elem_type, op1.get("val"), expression_node.elem_type, op2.get("val")))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") or op2.get("val")))
				case "==":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") == op2.get("val")))
				case "!=":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") != op2.get("val")))
				case "<":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") < op2.get("val")))
				case ">":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") > op2.get("val")))
				case "<=":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") <= op2.get("val")))
				case ">=":
					if op1.elem_type not in {InterpreterBase.INT_DEF, InterpreterBase.BOOL_DEF}:
						super().error(ErrorType.TYPE_ERROR, "Comparison not supported for type: {}".format(op1.elem_type))
					return Element(InterpreterBase.BOOL_DEF, val=(op1.get("val") >= op2.get("val")))
				
		elif expression_node.elem_type in self.unary_ops:
			op = self.evaluate_expression(expression_node.get("op1"))
			match expression_node.elem_type:
				case InterpreterBase.NOT_DEF:
					if op.elem_type != InterpreterBase.BOOL_DEF:
						super().error(ErrorType.TYPE_ERROR, "Type mismatch on unary operation: {} {}".format(expression_node.elem_type, op.get("val")))
					return Element(InterpreterBase.BOOL_DEF, val=(not op.get("val")))
				case InterpreterBase.NEG_DEF:
					if op.elem_type != InterpreterBase.INT_DEF:
						super().error(ErrorType.TYPE_ERROR, "Type mismatch on unary operation: {} {}".format(expression_node.elem_type, op.get("val")))
					return Element(InterpreterBase.INT_DEF, val=(-op.get("val")))
		else:
			super().error(ErrorType.TYPE_ERROR, "Unknown expression type: {}".format(expression_node.elem_type))

	# Setters and getters
 
	def set_function(self, func):
		self.functions["{}-{}".format(func.get("name"), len(func.get("args")))] = func
  
	def get_function(self, func_name, num_args):
		if self.functions.get("{}-{}".format(func_name, num_args)) != None:
			return self.functions["{}-{}".format(func_name, num_args)]
		else:
			super().error(ErrorType.NAME_ERROR, "Unknown Function Referenced: {}, taking {} args".format(func_name, num_args))
  
	def set_variable(self, var_name, value):
		var = None
		for frame in self.frames[::-1]:
			if frame.get(var_name) != None:
				frame[var_name] = value
				break
		if var == None:
			self.frames[-1][var_name] = value
  
	def get_variable(self, var_name):
		var = None
		for frame in self.frames[::-1]:
			if frame.get(var_name) != None:
				var = frame.get(var_name)
				break
		if var == None:
			super().error(ErrorType.NAME_ERROR, f"Unknown variable: {var_name}")
		return var