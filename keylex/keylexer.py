import typing

import sys


from pygments.token import *
from pygments.lexer import Lexer
import antlr4
from .KeYLexer import KeYLexer as AKL

# antlr4 -Dlanguage=Python3 MyGrammar.g4


SPECIAL = {
    AKL.WS: Whitespace,
    AKL.INT_LITERAL: Number,
    AKL.STRING_LITERAL: String,
    AKL.QUOTED_STRING_LITERAL: String.Double,
    AKL.DOC_COMMENT: String.Doc,
    AKL.FLOAT_LITERAL: Number.Float,
    AKL.CHAR_LITERAL: String.Char,
    AKL.COMMENT_END: Comment.Multiline,
    AKL.ML_COMMENT: Comment.Multiline,
    AKL.SL_COMMENT: Comment.Single,
    AKL.IDENT: Name.Variable,
    AKL.FALSE: Literal.Bool,
    AKL.TRUE: Literal.Bool,
    AKL.DOUBLE_LITERAL: Literal.Float,
    AKL.REAL_LITERAL: Literal.Float,
    AKL.ERROR_CHAR: Error,
    AKL.BIN_LITERAL: Number.Bin,
    AKL.HEX_LITERAL: Number.Hex,
}

OPERATORS = frozenset((AKL.LESS, AKL.LESSEQUAL, AKL.LGUILLEMETS, AKL.EQV, AKL.PRIMES,
                      AKL.EXP, AKL.TILDE, AKL.PERCENT, AKL.STAR, AKL.MINUS, AKL.PLUS, AKL.GREATER, AKL.GREATEREQUAL, AKL.SLASH,  AKL.ASSIGN,
                      AKL.AT, AKL.PARALLEL, AKL.OR, AKL.AND, AKL.NOT, AKL.IMP, AKL.EQUALS, AKL.NOT_EQUALS, AKL.SEQARROW, AKL.DOTRANGE))

PUNCTATION = frozenset((AKL.COMMA, AKL.LPAREN, AKL.RPAREN, AKL.LBRACE, AKL.RBRACE, AKL.LBRACKET, AKL.RBRACKET, AKL.SEMI,
                       AKL.COLON, AKL.DOUBLECOLON,
                       AKL.EMPTYBRACKETS, AKL.RGUILLEMETS, AKL.DOT))

KEYWORDS = frozenset((AKL.MODALITY, AKL.SORTS,
                     AKL.GENERIC, AKL.PROXY, AKL.EXTENDS, AKL.ONEOF, AKL.ABSTRACT, AKL.SCHEMAVARIABLES, AKL.SCHEMAVAR, AKL.MODALOPERATOR, AKL.PROGRAM, AKL.FORMULA,
                     AKL.TERM, AKL.UPDATE, AKL.VARIABLES, AKL.VARIABLE, AKL.SKOLEMTERM, AKL.SKOLEMFORMULA, AKL.TERMLABEL, AKL.MODIFIES, AKL.PROGRAMVARIABLES,
                     AKL.STORE_TERM_IN, AKL.STORE_STMT_IN, AKL.HAS_INVARIANT, AKL.GET_INVARIANT, AKL.GET_FREE_INVARIANT, AKL.GET_VARIANT,
                     AKL.IS_LABELED, AKL.SAME_OBSERVER, AKL.VARCOND, AKL.APPLY_UPDATE_ON_RIGID, AKL.DEPENDINGON, AKL.DISJOINTMODULONULL,
                     AKL.DROP_EFFECTLESS_ELEMENTARIES, AKL.DROP_EFFECTLESS_STORES, AKL.SIMPLIFY_IF_THEN_ELSE_UPDATE, AKL.ENUM_CONST, AKL.FREELABELIN,
                     AKL.HASSORT, AKL.FIELDTYPE, AKL.FINAL, AKL.ELEMSORT, AKL.HASLABEL, AKL.HASSUBFORMULAS, AKL.ISARRAY, AKL.ISARRAYLENGTH, AKL.ISCONSTANT,
                     AKL.ISENUMTYPE, AKL.ISINDUCTVAR, AKL.ISLOCALVARIABLE, AKL.ISOBSERVER, AKL.DIFFERENT, AKL.METADISJOINT, AKL.ISTHISREFERENCE,
                     AKL.DIFFERENTFIELDS, AKL.ISREFERENCE, AKL.ISREFERENCEARRAY, AKL.ISSTATICFIELD, AKL.ISINSTRICTFP, AKL.ISSUBTYPE, AKL.EQUAL_UNIQUE,
                     AKL.NEW, AKL.NEW_TYPE_OF, AKL.NEW_DEPENDING_ON, AKL.HAS_ELEMENTARY_SORT, AKL.NEWLABEL, AKL.CONTAINS_ASSIGNMENT, AKL.NOT_,
                     AKL.NOTFREEIN, AKL.SAME, AKL.STATIC, AKL.STATICMETHODREFERENCE, AKL.MAXEXPANDMETHOD, AKL.STRICT, AKL.TYPEOF, AKL.INSTANTIATE_GENERIC,
                     AKL.FORALL, AKL.EXISTS, AKL.SUBST, AKL.IF, AKL.IFEX, AKL.THEN, AKL.ELSE, AKL.INCLUDE, AKL.INCLUDELDTS, AKL.CLASSPATH, AKL.BOOTCLASSPATH,
                     AKL.NODEFAULTCLASSES, AKL.JAVASOURCE, AKL.WITHOPTIONS, AKL.OPTIONSDECL, AKL.KEYSETTINGS, AKL.PROFILE,
                     AKL.SAMEUPDATELEVEL, AKL.INSEQUENTSTATE, AKL.ANTECEDENTPOLARITY, AKL.SUCCEDENTPOLARITY, AKL.CLOSEGOAL,
                     AKL.HEURISTICSDECL, AKL.NONINTERACTIVE, AKL.DISPLAYNAME, AKL.HELPTEXT, AKL.REPLACEWITH, AKL.ADDRULES,
                     AKL.ADDPROGVARS, AKL.HEURISTICS, AKL.FIND, AKL.ADD, AKL.ASSUMES, AKL.TRIGGER, AKL.AVOID, AKL.PREDICATES,
                     AKL.FUNCTIONS, AKL.TRANSFORMERS, AKL.UNIQUE, AKL.RULES, AKL.AXIOMS, AKL.PROBLEM, AKL.CHOOSECONTRACT,
                     AKL.PROOFOBLIGATION, AKL.PROOF, AKL.PROOFSCRIPT, AKL.CONTRACTS, AKL.INVARIANTS, AKL.LEMMA, AKL.IN_TYPE,
                     AKL.IS_ABSTRACT_OR_INTERFACE, AKL.CONTAINERTYPE, AKL.UTF_PRECEDES, AKL.UTF_IN, AKL.UTF_EMPTY, AKL.UTF_UNION,
                     AKL.UTF_INTERSECT, AKL.UTF_SUBSET, AKL.UTF_SETMINUS,
                     AKL.MODALITYD, AKL.MODALITYB, AKL.MODALITYBB, AKL.MODAILITYGENERIC1,
                     AKL.MODAILITYGENERIC2, AKL.MODAILITYGENERIC3, AKL.MODAILITYGENERIC4, AKL.MODAILITYGENERIC5, AKL.MODAILITYGENERIC6, AKL.MODAILITYGENERIC7,
                     AKL.MODALITYD_END, AKL.MODALITYD_STRING, AKL.MODALITYD_CHAR, AKL.MODALITYG_END, AKL.MODALITYB_END, AKL.MODALITYBB_END))


__all__ = ('KeYLexer')


class KeYLexer(Lexer):
    name = 'KeY'
    aliases = ['key']
    filenames = ['*.key']

    def __init__(self, **options) -> None:
        super().__init__(**options)
        self.table = [None] * (AKL.MODALITYBB_END+1)
        for typ, style in SPECIAL.items():
            self.table[typ] = style

        styles = (Operator, Punctuation, Keyword)
        for style, typseq in zip(styles, (OPERATORS, PUNCTATION, KEYWORDS)):
            for typ in typseq:
                self.table[typ] = style

    def get_tokens_unprocessed(self, text: str):
        input_stream = antlr4.InputStream(text)
        lexer = AKL(input_stream)
        tokens: typing.List[antlr4.Token] = lexer.getAllTokens()

        for idx, token in enumerate(tokens):
            if token.type == AKL.INT_LITERAL:
                for lookahead in tokens[idx+1:]:
                    if lookahead.channel == 2:
                        continue
                    if lookahead.type == AKL.LPAREN:
                        token.setType(AKL.IDENT)
                    break

            clazz = self.class_for_type(token.type)
            if clazz is None:
                continue

            off = token.start
            value = token.text
            yield (off, clazz, value)

    def class_for_type(self, token: int):
        if v := self.table[token]:
            return v
        else:
            return Error
