#!/usr/bin/env python3

"""Data layout computation pass. Each symbol whose location (alloct)
is not a register, is allocated in the local stack frame (LocalSymbol) or in
the data section of the executable (GlobalSymbol)."""

import ir

class SymbolLayout(object):
    def __init__(self, symname, bsize):
        self.symname = symname
        self.bsize = bsize


class LocalSymbolLayout(SymbolLayout):
    def __init__(self, symname, fpreloff, bsize):
        self.symname = symname
        self.fpreloff = fpreloff
        self.bsize = bsize

    def __repr__(self):
        return self.symname + ": fp + (" + repr(self.fpreloff) + ") [def byte " + \
               repr(self.bsize) + "]"


class ParameterSymbolLayout(LocalSymbolLayout):
    def __repr__(self):
        return self.symname + ": parameter at offset " + repr(self.fpreloff) + " [def byte " + \
               repr(self.bsize) + "]"

class GlobalSymbolLayout(SymbolLayout):
    def __init__(self, symname, bsize):
        self.symname = symname
        self.bsize = bsize

    def __repr__(self):
        return self.symname + ": def byte " + repr(self.bsize)


def perform_data_layout(root):
    perform_data_layout_of_program(root)
    for defin in root.defs.children:
        perform_data_layout_of_function(defin)


def perform_data_layout_of_function(funcroot):
    offs = 0  # prev fp
    prefix = "_" + funcroot.symbol.name + "_"
    for var in funcroot.body.symtab:
        if var.stype.size == 0 or var.alloct == 'param':
            continue
        bsize = var.stype.size // 8
        offs -= bsize
        var.set_alloc_info(LocalSymbolLayout("_l" + prefix + var.name, offs, bsize))

    funcroot.body.stackroom = -offs + compute_space_for_parameter_passing(funcroot.body)

    offs = 0
    for var in reversed(funcroot.body.symtab):
        if var.stype.size == 0 or var.alloct != 'param':
            continue
        bsize = var.stype.size // 8
        var.set_alloc_info(ParameterSymbolLayout("_p" + prefix + var.name, offs, bsize))
        offs += bsize


def perform_data_layout_of_program(root):
    prefix = "_g_"
    for var in root.symtab:
        if var.stype.size == 0:
            continue
        var.set_alloc_info(GlobalSymbolLayout(prefix + var.name, var.stype.size // 8))
    root.stackroom = compute_space_for_parameter_passing(root)


### why not use push instead?
def compute_space_for_parameter_passing(block):
    max_params_size = 0
    def find_max_parameter_count(node):
        nonlocal max_params_size
        if type(node) == ir.BranchStat and node.returns:
            f = node.find_function_in_scope(node.target)
            max_params_size = max(max_params_size, sum([s.stype.size//8 for s in f.body.symtab if s.alloct == 'param']))

    block.navigate(find_max_parameter_count)
    return max_params_size
