import sys

import parsimonious as p

#Grammar

grammar = p.Grammar(
     """
         program  = space (fundef / expr)+
         space = ~"\s*"
         expr =  (funcall / ifelse / number / symbol) space
         number = ~"[0-9]+"
         symbol = ~"[a-z]+"
         funcall = symbol '[' args ']'
         args = expr*
         fundef = symbol space (symbol space)* ':' space expr space
         ifelse = '(' space expr ')' space expr '|' space expr
     """)


#Parser

class Bumpkin:
    
    def __init__(self, env={}):
        
        env["print"] = lambda *a: sys.stdout.write(' '.join(str(i) for i in a))
        env["sub"] = lambda a, b: a - b
        
        self.env = env
        
    def parse(self, source):
        return grammar['program'].parse(source)

    def evaluate(self, source):
        node = self.parse(source) if isinstance(source, str) else source
        method = getattr(self, node.expr_name, lambda node, children: children)

        if node.expr_name in ['ifelse', 'fundef']:
            return method(node)
        
        return method(node, [self.evaluate(n) for n in node])

    def program(self, node, children):
        ''' program  = space (expr)+ '''
        space, prog = children
        return prog

    def expr(self, node, children):
        ''' expr =  (number / symbol) space '''
        return children[0][0] #return the first expr of the first group

    def number(self, node, children):
        ''' number = ~"[0-9]+" '''
        return int(node.text)
    
    def space(self, node, children):
        ''' space = ~"\s*" '''
        
    def symbol(self, node, children):
        ''' symbol = ~"[a-z]+" '''
        return node.text.strip()

    def funcall(self, node, children):
        ''' funcall = sym '[' args ']' '''

        name, _, args, _ = children
        f = self.env.get(name)
        args = [self.env.get(a, a) for a in args] #hack add grammar for argname

        return f(*args)
    
    def args(self, node, children):
        return children
    
    def fundef(self, node):
        
        fname, _, params, _, _, expr, _ = node
        params = [self.evaluate(p) for p, _ in params]
        
        def f(*a):
            env = dict(self.env.items() + zip(params, a))
            return Bumpkin(env).evaluate(expr)
        
        self.env[fname.text] = f
        return f
    
    def params(self, node, children):
        return children
        
    def ifelse(self, node):
        
        _, _, cond, _, _, tbranch, _, _, fbranch = node

        if self.evaluate(cond):
            return self.evaluate(tbranch)
        else:
            return self.evaluate(fbranch)
        
        
if __name__ == "__main__":

    # 5 is the max
    program = '''

        eq x y: (sub[x y]) 0 | 1
        add a b: sub[a sub[0 b]]
        mul a b: (eq[b 0]) 0 | add[a mul[a sub[b 1]]]
        fact n: (eq[n 1]) 1 | mul[n fact[sub[n 1]]]
        print[fact[5]]
        
    '''
    Bumpkin().evaluate(program)
