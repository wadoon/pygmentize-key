
from pygments.lexer import Lexer
from pygments.lexers.jvm import JavaLexer
from pygments.token import *

from .JML import JML

from typing import List, Dict

import antlr4


class JMLLexer(Lexer):
    name = 'JML'
    aliases = ['jml', 'java-modeling-language']
    filenames = ['*.java', '*.jml']

    def __init__(self, **options) -> None:
        super().__init__(**options)
        self.java_lex = JavaLexer(**options)
        self.conditional_checker = JmlConditionalChecker()

    def get_tokens_unprocessed(self, text: str):
        for (index, kind, value) in self.java_lex.get_tokens_unprocessed(text):
            if kind == Comment.Single or kind == Comment.Multline:
                print(kind)
                yield from self.expand_jml(index, kind, value)
            else:
                yield (index, kind, value)

    def expand_jml(self, index, kind, text):
        # analyze the document and return semantic tokens
        # if (token.type == JML.JML_SET_KEY):
        #    conditionalChecker.setKeysFromToken(token)
        #    continue

        if not self.conditional_checker.isActive(text):
            yield (index, kind, text)
        else:
            start = text.find("@") + 1
            offset = index + start 

            yield (index, Comment.Preproc, text[:start])

            lexer = JML(antlr4.InputStream(text[start:]))
            lexer._mode = JML.jmlMode

            parenthesisLevel = 0
            bracesLevel = 0
            bracketLevel = 0
            waitForToplevelSemicolon = False

            for token in lexer.getAllTokens():
                offset = token.start + start
                level0 = bracketLevel == 0 and bracesLevel == 0 and parenthesisLevel == 0
                toplevel = not waitForToplevelSemicolon and level0

                match token.type:
                    case JML.LPAREN: parenthesisLevel += 1
                    case JML.RPAREN: parenthesisLevel -= 1
                    case JML.LBRACE: bracesLevel += 1
                    case JML.RBRACE: bracesLevel -= 1
                    case JML.LBRACE: bracketLevel += 1
                    case JML.RBRACE: bracketLevel -= 1
                    case JML.SEMI:
                        if level0:
                            waitForToplevelSemicolon = False

                if token.type in TYPE2TYPE:
                    kind = TYPE2TYPE[token.type]
                else:
                    kind = TYPE2TYPE[(token.type, toplevel)]

                if token.type == JML.JML_KEYWORDS_TL_EXPR and toplevel:
                    waitForToplevelSemicolon = True

                yield (offset, kind, token.text)


TYPE2TYPE = {
    JML.WS: Whitespace,
    JML.LPAREN: Punctuation,
    JML.RPAREN: Punctuation,
    JML.LBRACE: Punctuation,
    JML.RBRACE: Punctuation,
    JML.LBRACK: Punctuation,
    JML.RBRACK: Punctuation,
    JML.SEMI: Punctuation,
    JML.JAVA_MODIFIERS: Keyword,
    JML.JML_KEYWORDS_ALWAYS: Keyword,
    JML.JAVA_KEYWORDS: Keyword,
    (JML.JML_MODIFIERS, True): Keyword,
    (JML.JML_MODIFIERS, False): Name.Variable,
    (JML.JML_KEYWORDS_TL_EXPR, True): Keyword,
    (JML.JML_KEYWORDS_TL, True): Keyword,
    (JML.JML_KEYWORDS_TL, True): Name.Variable,
    JML.IDENTIFIER: Name.Variable,
    JML.NUM_LITERALS: Number,
    JML.COMMENT: Comment,
    JML.ASSIGN: Operator,
    JML.GT: Operator,
    JML.LT: Operator,
    JML.BANG: Operator,
    JML.TILDE: Operator,
    JML.QUESTION: Operator,
    JML.COLON: Operator,
    JML.EQUAL: Operator,
    JML.LE: Operator,
    JML.GE: Operator,
    JML.NOTEQUAL: Operator,
    JML.AND: Operator,
    JML.OR: Operator,
    JML.INC: Operator,
    JML.DEC: Operator,
    JML.ADD: Operator,
    JML.SUB: Operator,
    JML.MUL: Operator,
    JML.DIV: Operator,
    JML.BITAND: Operator,
    JML.BITOR: Operator,
    JML.CARET: Operator,
    JML.MOD: Operator,
    JML.ADD_ASSIGN: Operator,
    JML.SUB_ASSIGN: Operator,
    JML.MUL_ASSIGN: Operator,
    JML.DIV_ASSIGN: Operator,
    JML.AND_ASSIGN: Operator,
    JML.OR_ASSIGN: Operator,
    JML.XOR_ASSIGN: Operator,
    JML.MOD_ASSIGN: Operator,
    JML.LSHIFT_ASSIGN: Operator,
    JML.RSHIFT_ASSIGN: Operator,
    JML.URSHIFT_ASSIGN: Operator,
    JML.ARROW: Operator,
    JML.COLONCOLON: Operator,
    JML.DOTDOT: Operator,
    JML.EQUIVALENCE: Operator,
    JML.ANTIVALENCE: Operator,
    JML.IMPLIES: Operator,
    JML.IMPLIESBACKWARD: Operator,
    JML.LOCKSET_LEQ: Operator,
    JML. LOCKSET_LT: Operator,
    JML.ST: Operator,
    JML.AT: Operator,
    JML.ELLIPSIS: Operator,
    JML.ERROR_CHAR: Error,
}


class JmlConditionalChecker:
    def __init__(self) -> None:
        # currently activated keys
        self.activeKeys: List[str] = []
        #
        self.cache: Dict[str, bool] = {}

    def isActive(self, text: str) -> bool:
        if text:
            atSign = text.find('@')
            keys = text.strip()[2: atSign]
            cachedValue = self.cache.get(keys, None)
            if cachedValue:
                return cachedValue

            conditions = keys.split("/(?=[+-])/")
            result = self.isActiveForConditions(conditions)
            self.cache[keys] = result
            return result
        return False

    def isActiveForConditions(self, conditions: List[str]) -> bool:
        # a JML annotation with at least one positive-key is only included
        plusKeyFound = False
        # if at least one of these positive keys is enabled
        enabledPlusKeyFound = False

        # a JML annotation with an enabled negative-key is ignored (even if there are enabled positive-keys).
        enabledNegativeKeyFound = False

        for marker in conditions:
            if marker is None or marker == "":
                continue
            isPositive = marker[0] == '+'
            isNegative = not isPositive
            k = marker[1:].lower()
            isEnabled = any((x == k for x in self.activeKeys))
            plusKeyFound = plusKeyFound or isPositive
            enabledPlusKeyFound = enabledPlusKeyFound or isPositive and isEnabled
            enabledNegativeKeyFound = enabledNegativeKeyFound or isNegative and isEnabled
            if "-" == marker or "+" == marker:  # old deprecated conditions
                return False

        return (not plusKeyFound or enabledPlusKeyFound) and not enabledNegativeKeyFound

    def setKeysFromToken(self, token: Token):
        """Given a JML_SET_KEY token, this method sets the active keys for deciding the inclusion of
        conditional JML annotation comments. """
        # JML_SET_KEY: '//-*- jml-keys: ' (IDENTIFIER)* '-*-';
        prefix = "//-*- jml-keys: "
        suffix = ""  # "-*-"
        text = token.text
        if text:
            content = text.substring(len(prefix), text.length - len(suffix))
            keys = content.split("[ ,]")
            self.activeKeys = [k.strip().lowercase() for k in keys]
            self.cache.clear()
