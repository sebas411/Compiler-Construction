.text

.globl main

main:
    jal     ask_numbers
    la		$t0, var_a
    lw      $a0, 0($t0)
    la      $t0, var_b
    lw      $a1, 0($t0)
    
    jal		mcd				# mcd(a,b)

    la		$t0, var_a
    lw      $a0, 0($t0)
    la      $t0, var_b
    lw      $a1, 0($t0)
    move    $a2, $v0
    jal     print_result

    #exit
    li		$v0, 10
    syscall
    
ask_numbers:
    li		$v0, 4
    la		$a0, ask1
    syscall
    li      $v0, 5
    syscall
    la      $t0, var_a
    sw      $v0, 0($t0)

    li		$v0, 4
    la		$a0, ask2
    syscall
    li      $v0, 5
    syscall
    la      $t0, var_b
    sw      $v0, 0($t0)
    jr      $ra

#mcd(a,b):
#   if a == 0: return b
#   if b == 0: return a
#   r = a % b
#   return mcd(b,r)
mcd:
    move 	$v0, $a0		# r = a
    beqz	$a1, exit_mcd	# if b == 0 goto exit
    move 	$v0, $a1		# r = b
    beqz	$a0, exit_mcd	# if a == 0 goto exit

    div		$a0, $a1		# a / b
    mfhi	$t0				# $t0 = a % b
    move    $a0, $a1        # a = b
    move    $a1, $t0        # b = r
    sub     $sp, $sp, 4		# $sp = $sp - 4
    sw		$ra, 0($sp)		# sp[0] = ra
    jal		mcd				# mcd(b,r)
    lw		$ra, 0($sp)		# ra = sp[0]
    addi	$sp, $sp, 4		# $sp = $sp + 4
    
exit_mcd:
    jr      $ra
    
print_result:
    move    $t0, $a0
    li		$v0, 4
    la		$a0, msg1
    syscall             # "El maximo comun divisor entre "
    move    $a0, $t0
    li      $v0, 1
    syscall             # a
    li		$v0, 4
    la		$a0, msg2
    syscall             # " y "
    move    $a0, $a1
    li      $v0, 1
    syscall             # b
    li		$v0, 4
    la		$a0, msg3
    syscall             # "es: "
    move    $a0, $a2
    li      $v0, 1
    syscall             # res
    li		$v0, 4
    la		$a0, msg4
    syscall             # "\n"
    jr      $ra


.data
var_a:      .word   0
var_b:      .word   0

msg1:   .asciiz "\nEl maximo comun divisor entre "
msg2:   .asciiz " y "
msg3:   .asciiz " es: "
msg4:   .asciiz "\n"

ask1:   .asciiz "Bienvenido al programa para calcular el maximo comun divisor :)\nPor favor ingrese el primer entero: "
ask2:   .asciiz "Por favor ingrese el segundo entero: "
