grammar YAPL;

CLASS: 'class';
ELSE: 'else';
FI: 'fi';
IF: 'if';
IN: 'in';
INHERITS: 'inherits';
ISVOID: 'isvoid';
LOOP: 'loop';
POOL: 'pool';
THEN: 'then';
WHILE: 'while';
NEW: 'new';
NOT: 'not';
FALSE: 'false';
TRUE: 'true';

TYPE_ID: 'self_type' | 'self' | [A-Z][a-zA-Z0-9_]*; 
OBJECT_ID:  [a-z][a-zA-Z0-9_]*;

STRING: '"' (~["\\\u0000-\u001F] | '\\' (["\\/bfnrt] | 'u' [0-9a-fA-F]{4}))* '"';
LINE_COMMENT:'--' .*? [\n\r] -> skip;
BLOCK_COMMENT: ('(*' .*? '*)') -> skip;
INTEGER: [0-9]+;
WS: [ \t\n\r\f] + -> skip;

source: class_prod+ EOF;
class_prod: CLASS TYPE_ID (INHERITS TYPE_ID)? '{' (feature ';')* '}' ';';
id: OBJECT_ID;
feature: id '(' (formal (',' formal)* )? ')' ':' TYPE_ID '{' expr '}'                     
        | id ':' TYPE_ID ('<-' expr)?                                                     
        ;
formal: id ':' TYPE_ID ;
expr: expr ('@' TYPE_ID)? '.'id '(' (expr (',' expr)*)? ')'                           
        | id '(' (expr (',' expr)*)? ')'                                                  
        | IF expr THEN expr ELSE expr FI                                                   
        | WHILE expr LOOP expr POOL                                                        
        | '{' (expr ';')+ '}'                                                              
        | 'let' id ':' TYPE_ID ('<-' expr)? (',' id ':' TYPE_ID ('<-' expr)?)* 'in' expr   
        | NEW TYPE_ID                                                                      
        | ISVOID expr                                                                      
        | expr '+' expr
        | expr '-' expr                                                                    
        | expr '*' expr                                                                    
        | expr '/' expr                                                                   
        | ('-'|'~') expr                                                                   
        | expr '<' expr                                                                    
        | expr '<=' expr                                                                   
        | expr '=' expr                                                                    
        | NOT expr                                                                         
        | '(' expr ')'                                                                     
        | id '<-' expr 
        | id                                                                               
        | INTEGER                                                                          
        | STRING                                                                           
        | TRUE                                                                             
        | FALSE                                                                            
        | 'self'                                                                           
        ;
