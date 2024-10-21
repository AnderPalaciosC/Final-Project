from werkzeug.security import generate_password_hash

# Define la contraseña que quieres hashear
password = '2163'

# Genera el hash de la contraseña
hashed_password = generate_password_hash(password)

# Imprime el hash generado
print(hashed_password)