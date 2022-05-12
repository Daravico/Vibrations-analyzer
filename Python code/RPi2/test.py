import time

i = 5
while True:
	i= i-1
	try:
		x = 5 / i
		print(f'Dentro: {x}')
	except:
		print('# -----------------------')
		print('#      ------   Llegaste al zero')
		print('# ------------------------')
		continue

	time.sleep(1)
	print(f'Este valor: {i}')

