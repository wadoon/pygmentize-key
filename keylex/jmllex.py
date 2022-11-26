
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
        active_keys = options.get("active-keys", list())
        self.conditional_checker = JmlConditionalChecker(active_keys)
        super().__init__(**options)
        self.java_lex = JavaLexer(**options)

    def get_tokens_unprocessed(self, text: str):
        for (index, kind, value) in self.java_lex.get_tokens_unprocessed(text):
            if kind == Comment.Single or kind == Comment.Multiline:
                yield from self.expand_jml(index, kind, value)
            else:
                yield (index, kind, value)

    def expand_jml(self, index, kind, text):
        # analyze the document and return semantic tokens
        # if (token.type == JML.JML_SET_KEY):
        #    conditionalChecker.setKeysFromToken(token)
        #    continue

        if not self.conditional_checker.is_active(text):
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
                    kind = TYPE2TYPE.get((token.type, toplevel), Error)

                if token.type == JML.JML_KEYWORDS_TL and toplevel:
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
    (JML.JML_KEYWORDS_TL_EXPR, False): Keyword,
    (JML.JML_KEYWORDS_TL, True): Keyword,
    (JML.JML_KEYWORDS_TL, False): Name.Variable,
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
    def __init__(self, active_keys = None):
        # currently activated keys
        self.active_keys: List[str] = set(active_keys) if active_keys else list()
        self.cache: Dict[str, bool] = {}

    def is_active(self, text: str) -> bool:
        at_sign = text.find('@')
        keys = text.strip()[2: at_sign]
        cached_value = self.cache.get(keys, None)
        if cached_value:
            return cached_value

        conditions = keys.split("/(?=[+-])/")
        result = self.is_active_for_conditions(conditions)
        self.cache[keys] = result
        return result

    def is_active_for_conditions(self, conditions: List[str]) -> bool:
        # a JML annotation with at least one positive-key is only included
        plus_key_found = False
        # if at least one of these positive keys is enabled
        enabled_plus_key_found = False

        # a JML annotation with an enabled negative-key is ignored (even if there are enabled positive-keys).
        enabled_negative_key_found = False

        for marker in conditions:
            if marker is None or marker == "":
                continue
            is_positive = marker[0] == '+'
            is_negative = not is_positive
            k = marker[1:].lower()
            is_enabled = any((x == k for x in self.active_keys))
            plus_key_found = plus_key_found or is_positive
            enabled_plus_key_found = enabled_plus_key_found or is_positive and is_enabled
            enabled_negative_key_found = enabled_negative_key_found or is_negative and is_enabled
            if "-" == marker or "+" == marker:  # old deprecated conditions
                return False

        return (not plus_key_found or enabled_plus_key_found) and not enabled_negative_key_found

    def set_keys_from_token(self, token: Token):
        """Given a JML_SET_KEY token, this method sets the active keys for deciding the inclusion of
        conditional JML annotation comments. """
        # JML_SET_KEY: '//-*- jml-keys: ' (IDENTIFIER)* '-*-';
        prefix = "//-*- jml-keys: "
        suffix = ""  # "-*-"
        text = token.text
        if text:
            content = text.substring(len(prefix), text.length - len(suffix))
            keys = content.split("[ ,]")
            self.active_keys = [k.strip().lowercase() for k in keys]
            self.cache.clear()
