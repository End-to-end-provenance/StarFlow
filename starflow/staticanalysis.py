#!/usr/bin/env python
'''
Static analysis routines.

'''

import inspect
from starflow.utils import *
import ast

def GetFullUses(FilePath):
	'''
	Adds information about actual paths in  existence in the file system to further
	refine results of the GetUses function.

	Argument:
	--FilePath = path to file of module to do static analysis of.

	Returns:
	If call to GetUses Fails, then: None, else, a dictionary F, where:
	-- the keys are names of objects defined in the module in FilePath
	and
	-- for the key 'Obj', the value F['Obj']  is a list of pairs

		(objname,file)

		where objname is the name of an object that is referenced
		somwhere in the definition of 'Obj' and file is the name of the
		file where objname is defined.

	'''

	ModuleName = FilePath.lstrip('../').rstrip('.py').replace('/','.')
	print("Get full uses " +ModuleName)

	try:
		[F,M,N] = GetUses(FilePath=FilePath)
	except:
		return None
	else:
		pass


	Mentions = ListUnion(list(F.values()))

	#internals as those things in mentions that are in N.keys() + F.keys()
	ModuleName = FilePath[3:-3].replace('/','.')
	Internals = set(Mentions).intersection(list(N.keys()) + list(F.keys()))
	InternalRefs = dict([(x,(ModuleName+'.'+x,FilePath)) for x in Internals])


	[Externals,StarUses,MoreInternals] = usechecking(Mentions,M,N,FilePath,ModuleName,Internals,'__module__')


	FF = {}
	for k in list(F.keys()):
		[LocalExternals, LocalStarUses, LocalMoreInternals] = usechecking(Mentions,M,N,FilePath,ModuleName,Internals,k)
		LocalExternals.update(Externals) ; LocalStarUses.update(StarUses) ; LocalMoreInternals.update(MoreInternals)

		A = []
		for t in [InternalRefs,LocalExternals,LocalStarUses,LocalMoreInternals]:
			A += [t[l] for l in F[k] if l in list(t.keys())]
		A = uniqify(A)
		B = [l for l in F[k] if l not in list(InternalRefs.keys()) + list(LocalExternals.keys()) + list(LocalStarUses.keys()) + list(LocalMoreInternals.keys())]
		FF[k] = [A,B]
	for k in list(N.keys()):
		[LocalExternals, LocalStarUses, LocalMoreInternals] = usechecking(Mentions,M,N,FilePath,ModuleName,Internals,k)
		LocalExternals.update(Externals) ; LocalStarUses.update(StarUses) ; LocalMoreInternals.update(MoreInternals)
		A = []
		for t in [InternalRefs,Externals,StarUses,MoreInternals]:
			A += [t[l] for l in N[k] if l in list(t.keys())]
		A = uniqify(A)
		B = [l for l in N[k] if l not in list(InternalRefs.keys()) + list(LocalExternals.keys()) + list(LocalStarUses.keys()) + list(LocalMoreInternals.keys())]
		FF[k] = [A,B]

	return FF


def usechecking(Mentions,M,N,FilePath,ModuleName,Internals,key):

	if key in list(M.keys()):
		M = M[key]
		Imported = [] ; Imports = []
		for x in Mentions:
			if x in list(M.keys()):
				Imported += [(x,M[x])]
				Imports += [(x,x)]
			elif any([x.startswith(m + '.') for m in list(M.keys())]):
				H =  [m for m in list(M.keys()) if x.startswith(m + '.')]
				Imports += [(x,h) for h in H]
				Imported += [(x,M[h] + x[len(h):]) for h in H]
		Externals = {}
		for (x,y) in Imported:

			paths1 = ['../' + '/'.join(y.split('.')[:j]) + '.py' for j in range(len(y.split('.'))) if IsFile('../' + '/'.join(y.split('.')[:j]) + '.py')]
			paths2 = ['../' + '/'.join(y.split('.')[:j])  + '/' for j in range(1,len(y.split('.'))) if IsDir('../' + '/'.join(y.split('.')[:j]))]

			if paths1:
				Externals[x] = (y,paths1[-1])
			elif paths2:
				Externals[x] = (y,paths2[-1])


		MoreInternals = dict([(x,(ModuleName + '.' + h,FilePath)) for (x,h) in Imports])

		Remainder = set(Mentions).difference(set([x[0] for x in Imports]).union(Internals))
		StarUses = []
		if len(Remainder) > 0:
			StarImports = [y[:-2] for y in list(N.keys()) if is_string_like(y) and y.endswith('.*')]
			for si in StarImports:
				sip = '../' + si.replace('.','/') + '.py'
				if IsFile(sip):
					[F1,M1,N1] = GetUses(FilePath = sip)
					StarUses += [(r,(si + '.' + r,sip)) for r in Remainder.intersection(list(F1.keys()) + list(N1.keys()))]

		StarUses = dict(StarUses)
	else:
		Externals = {} ; StarUses = {}; MoreInternals = {}

	return [Externals,StarUses,MoreInternals]

def GetUses(AST = None,FilePath=None):
	'''
	Gets information about the names referenced in a python module or AST
	fragment by doing static code analysis.

	ARGUMENTS:
	--AST = pre-compiler parse tree code object,
		e.g. result of calling compiler.parse() on some code fragment
	--FilePath = Path to python module
	One or the other but not both of these two arguments must be given

	RETURNS:
	None, if FilePath is given and call to compiler.parseFile() fails, else:
	AST is either given or generated frm the FilePath code returns a 3-element
	list [F,M,N] where:
	---F = dictionary, where:
		the keys are names of scopes (e.g. classes and functions) defined in the AST
		the values are names of functions and names mentioned in the functions
	--M = list of modules imported or used in the AST
	--N = dictionary where
		-- the keys are names of non-scoping names (those besides functions or classes)
		defined in the AST
		-- the value associated with key 'X' is list of other names
		by which X is known in the AST scope, including its definition
		in terms of imported modules
	'''

	if AST == None:
		assert FilePath != None, 'FilePath or AST must be specified'
		try:
			AST_str = open(FilePath).read()
			AST = ast.parse(AST_str)
		except:
			print(FilePath, 'failing to compile.')
			return None
		else:
			pass

	NameDefs = {}
	NamesUsage = {}
	ModuleUsage = {}
	GetUsesFromAST(AST,NameDefs, ModuleUsage, NamesUsage,'__module__')

	# print("NameDefs")
	# for entry in NameDefs:
	# 	print(entry)
	# 	print(NameDefs[entry])
	# print("ModuleUsage")
	# for entry in ModuleUsage:
	# 	print(entry)
	# 	print(ModuleUsage[entry])
	# print("NamesUsage")
	# for entry in NamesUsage:
	# 	print(entry)
	# 	print(NamesUsage[entry])

	return [NamesUsage,ModuleUsage,NameDefs] # check the ordering here. want FMN. NameDefs, ModuleUsage, NamesUsage??

def GetUsesFromAST(e, NameDefs, ModuleUsage, NamesUsage , CurScopeName):
	'''
		Recursive function which implements guts of static analysis.
		Documentation for _astmodule at:
		https://greentreesnakes.readthedocs.io/en/latest/manipulating.html#inspecting-nodes
	'''

	if isinstance(e,ast.Import):

		for l in e.names:
			if CurScopeName not in ModuleUsage:
				ModuleUsage[CurScopeName] = {}
			if l.asname != None:
				NameDefs[l.asname] = [l.asname]

				ModuleUsage[CurScopeName][l.asname] = l.name
			else:
				NameDefs[l.name] = [l.name]
				ModuleUsage[CurScopeName][l.name] = l.name

	elif isinstance(e,ast.YieldFrom):
		# changed from "From" to "YieldFrom"
		modulename = e.getChildren()[0]
		for f in e.getChildren()[1]:
			attname = f[0]
			fullname = modulename + '.' + attname
			localname = f[0] if f[1] is None else f[1]
			localname = localname if localname != '*' else fullname
			NameDefs[localname] = [localname]
			if CurScopeName not in ModuleUsage:
				ModuleUsage[CurScopeName] = {}
			ModuleUsage[CurScopeName][localname] = fullname


	elif isinstance(e,ast.If):
		NewND = NameDefs.copy()
		Children = ProperOrder(ast.iter_child_nodes(e))
		for f in Children:
			GetUsesFromAST(f,NewND,ModuleUsage, NamesUsage,CurScopeName)
		for l in list(NewND.keys()):
			if not NewND[l] is None:
				DictionaryOfListsAdd(NameDefs,l,NewND[l])


	elif isinstance(e,ast.ClassDef):
		NewND = NameDefs.copy()
		fname = e.getChildren()[0]
		if fname not in list(NamesUsage.keys()):
			NamesUsage[fname] = []
		Children = ProperOrder(ast.iter_child_nodes(e)())
		NewFU = {}
		for f in Children:
			GetUsesFromAST(f,NewND,ModuleUsage,NewFU,'__module__')
		for l in list(NewFU.keys()):
			NamesUsage[fname] += NewFU[l]


	elif isinstance(e,ast.Call):
		NewND = NameDefs.copy()
		fname = e.getChildren()[1]
		fvars = e.getChildren()[2]
		if fname not in list(NamesUsage.keys()):
			NamesUsage[fname] = []
		Children = ProperOrder(ast.iter_child_nodes(e)())
		NewFU = {}
		for f in Children:
			GetUsesFromAST(f,NewND,ModuleUsage, NewFU,fname)
		for l in list(NewFU.keys()):
			NamesUsage[fname] += [g for g in NewFU[l] if g.split('.')[0] not in fvars and g not in list(NewFU.keys())]

	elif isinstance(e,ast.Lambda):
		NewND = NameDefs.copy()
		fvars = e.argnames
		Children = ProperOrder(ast.iter_child_nodes(e)())
		for f in Children:
			GetUsesFromAST(f,NewND,ModuleUsage, NamesUsage,CurScopeName)
		NamesUsage[CurScopeName] = [g for g in NamesUsage[CurScopeName] if g.split('.')[0] not in fvars]

	elif isinstance(e,ast.ListComp):
		ForLoops = e.getChildren()[1:]
		LoopVars = [f.getChildren()[0].getChildren()[0] for f in ForLoops]
		Children = ProperOrder(ast.iter_child_nodes(e)())
		for f in Children:
			GetUsesFromAST(f,NameDefs,ModuleUsage, NamesUsage,CurScopeName)
		NamesUsage[CurScopeName] = [g for g in NamesUsage[CurScopeName] if g.split('.')[0] not in LoopVars]

	elif isinstance(e,ast.For):
		if isinstance(e.target,ast.Tuple):
			LoopControlVars = [ee.getChildren()[0] for ee in e.target.getChildren()]
		else:
			LoopControlVars = [e.target.id]

		Children = ProperOrder(ast.iter_child_nodes(e))
		for f in Children:
			GetUsesFromAST(f,NameDefs,ModuleUsage, NamesUsage,CurScopeName)
		NamesUsage[CurScopeName] = [g for g in NamesUsage[CurScopeName] if g.split('.')[0] not in LoopControlVars]


	elif isinstance(e,ast.Assign):
		Children = ProperOrder(ast.iter_child_nodes(e))
		for f in Children:
			GetUsesFromAST(f,NameDefs,ModuleUsage, NamesUsage,CurScopeName)

		if isinstance(Children[0],ast.List) or isinstance(Children[0],ast.Tuple):
			newnames = [ee.getChildren()[0] for ee in e.getChildren()[0].getChildren()]
			targs = e.getChildren()[1]
			if isinstance(targs, ast.List) or isinstance(targs, ast.Tuple):
				assignmenttargets = e.getChildren()[1].getChildren()
				assert len(newnames) == len(assignmenttargets), 'Wrong number of values to unpack.'
				for (newname,assignmenttarget) in zip(newnames,assignmenttargets):
					INT = interpretation(assignmenttarget,NameDefs)
					if INT == [] and CurScopeName == '__module__':
						NameDefs[newname] = [newname]
					else:
						NameDefs[newname] = INT
			else:
				assignmenttarget = e.getChildren()[1]
				INT = interpretation(assignmenttarget,NameDefs)
				for newname in newnames:
					if INT == [] and CurScopeName == '__module__':
						NameDefs[newname] = [newname]
					else:
						NameDefs[newname] = INT

		else:
			newname = e.targets
			assignmenttarget = e.value
			INT = interpretation(assignmenttarget,NameDefs)[:]
			for n in newname: #added loop here
				if INT == [] and CurScopeName == '__module__':
					NameDefs[n] = [n]
				else:
					NameDefs[n] = INT


	elif isinstance(e,ast.Attribute) or isinstance(e,ast.Name):
		attnameset = interpretation(e,NameDefs)[:]
		if not (attnameset is None):
			DictionaryOfListsAdd(NamesUsage,CurScopeName,attnameset)

		if attnameset != []:
			Children = ProperOrder(ast.iter_child_nodes(e))[1:]
		else:
			Children = ProperOrder(ast.iter_child_nodes(e))
		for f in Children:
			GetUsesFromAST(f,NameDefs,ModuleUsage, NamesUsage,CurScopeName)

	else:
		Children = ProperOrder(ast.iter_child_nodes(e))
		for f in Children:
			GetUsesFromAST(f,NameDefs,ModuleUsage, NamesUsage,CurScopeName)

def ProperOrder(NodeList):
	'''
	Order a list of AST nodes so that their analysis happens in proper for name defintions to be taken into account -- e.g. nonscope nodes first, then scope nodes.
	'''

	SameScopeChildren = [e for e in NodeList if not (isinstance(e,ast.Call) or isinstance(e,ast.ClassDef))]
	NewScopeChildren = [e for e in NodeList if isinstance(e,ast.Call) or isinstance(e,ast.ClassDef)]
	return SameScopeChildren + NewScopeChildren

def interpretation(n, NameDefs):
	'''
	determine "real" name(s) of a getattr or name ast node
	in terms of names of its pieces
	'''

	if isinstance(n,ast.Attribute) or isinstance(n,ast.Name):
		nameseq = UnrollGetatt(n)
		if nameseq != None:
			if nameseq[0] in list(NameDefs.keys()):
				if len(nameseq) > 1:
					return [l + '.' + '.'.join(nameseq[1:]) for l in NameDefs[nameseq[0]]]
				else:
					return NameDefs[nameseq[0]]
			else:
				return ['.'.join(nameseq)]
		else:
			return []
	else:
		return []



def UnrollGetatt(getseq):
	'''
	unrolls a Name or GetAttr compiler ast node into a dot-separated string name.
	'''

	if isinstance(getseq,ast.Name):
		# return [getseq.getChildren()[0]]
		return getseq.id
	elif isinstance(getseq,ast.Attribute):
		lowerlevel = UnrollGetatt(getseq.getChildren()[0])
		if not (lowerlevel is None):
			return lowerlevel + [getseq.getChildren()[1]]

def DictionaryOfListsAdd(D,key,newitem):
	if key in list(D.keys()):
		intersect = list(set(newitem).difference(D[key]))
		if len(intersect) > 0:
			D[key].extend(intersect)
	else:
		D[key] = newitem

# def FastTopNames(FilePath):
# 	try:
# 		AST = compiler.parseFile(FilePath)
# 	except:
# 		print FilePath, 'failing to compile.'
# 		return None
# 	else:
# 		pass
# 	Scopes = [l for l in AST.getChildren()[1] ]

def main():
    GetUses(FilePath = "/Users/jen/Desktop/PF/scripts/script.py")
	# GetFullUses(FilePath = "/Users/jen/Desktop/PF/scripts/script.py")

if __name__ == "__main__":
    main()
