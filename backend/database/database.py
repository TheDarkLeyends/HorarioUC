import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
import mysql.connector
import backend.database.constants as c
import global_constants as gc
from backend.database.tables import SectionDTO, CourseDTO

class Database:
    # Conexión y cursor
    def __init__(self):
        self.host = c.DATABASE_CREDENTIALS["host"]
        self.usuario = c.DATABASE_CREDENTIALS["user"]
        self.contrasena = c.DATABASE_CREDENTIALS["password"]
        self.conexion_cerrada = False
        
        try:
            self.conector = mysql.connector.connect(
                host=self.host, 
                user=self.usuario, 
                password=self.contrasena, 
                database=c.DATABASE_NAME
            )
            self.cursor = self.conector.cursor(dictionary=True)
            print("Se abrió la conexión con el servidor.")
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.conector = mysql.connector.connect(
                    host=self.host, 
                    user=self.usuario, 
                    password=self.contrasena
                )
                self.cursor = self.conector.cursor(dictionary=True)
                try:
                    self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {c.DATABASE_NAME}")
                    print(f"Se creó la base de datos {c.DATABASE_NAME} o ya estaba creada.")
                except:
                    print(f"Ocurrió un error al intentar crear la base de datos {c.DATABASE_NAME}.")
                self.conector.database = c.DATABASE_NAME
                print("Se creó la base de datos y se abrió la conexión con el servidor.")
                self.crear_tablas()
            else:
                raise Exception(f"Failed to connect to MySQL: {err}")

    # Decorador para el cierre del cursor y la base de datos
    def conexion(funcion_parametro):
        def interno(self, *args, **kwargs):
            try:
                if self.conexion_cerrada:
                    self.conector = mysql.connector.connect(
                        host=self.host, user=self.usuario, password=self.contrasena, database=c.DATABASE_NAME
                    )
                    self.cursor = self.conector.cursor(dictionary=True)
                    self.conexion_cerrada = False
                # Se llama a la función externa
                result = funcion_parametro(self, *args, **kwargs)  # type: ignore
                return result
            except Exception as e:
                # Se informa de un error en la llamada
                print("Ocurrió un error con la llamada.")
                print(e)
            finally:
                if self.conexion_cerrada:
                    pass
                else:
                    # Cerramos el cursor y la conexión
                    self.cursor.close()
                    self.conector.close()
                    self.conexion_cerrada = True

        return interno

    @conexion
    def crear_tabla(self, nombre_tabla: str, columnas: list[dict]):
        try:
            # String para guardar el string con las columnas y tipos de datos
            columnas_string = ""
            # Lista para guardar las claves primarias
            primary_keys = []
            # Lista para guardar las claves foráneas
            foreign_keys = []
            # Se itera la lista que se le pasa como argumento (cada diccionario)
            for columna in columnas:
                # formamos el string con nombre, tipo y longitud
                if columna["type"].lower() in ["bool", "boolean", "json"]:
                    columnas_string += f"{columna['name']} {columna['type']}"
                else:
                    columnas_string += (
                        f"{columna['name']} {columna['type']}({columna['length']})"
                    )
                # Si es clave primaria, auto_increment o no admite valores nulos, lo añade al string
                if columna.get("primary_key", False):
                    primary_keys.append(columna["name"])
                if columna.get("auto_increment", False):
                    columnas_string += " AUTO_INCREMENT"
                if columna.get("not_null", False):
                    columnas_string += " NOT NULL"
                if columna.get(
                    "unique", False
                ):  # Check if 'unique' key exists and if it's set to True
                    columnas_string += " UNIQUE"
                if "foreign_key" in columna:
                    foreign_keys.append(
                        (
                            columna["name"],
                            columna["foreign_key"]["table"],
                            columna["foreign_key"]["column"],
                            columna["foreign_key"].get("on_delete", "NO ACTION"),
                        )
                    )
                # Hace un salto de línea después de cada diccionario
                columnas_string += ",\n"
            # Elimina al final del string el salto de línea y la coma
            columnas_string = columnas_string[:-2]
            # Si hay claves primarias, se añaden al string
            if primary_keys:
                columnas_string += ",\n"
                columnas_string += "PRIMARY KEY (" + ",".join(primary_keys) + ")"
            # Si hay claves foráneas, se añaden al string
            for fk in foreign_keys:
                columnas_string += ",\n"
                columnas_string += f"FOREIGN KEY ({fk[0]}) REFERENCES {fk[1]}({fk[2]}) ON DELETE {fk[3]}"
            # Se crea la tabla juntando la instrucción SQL con el string generado
            sql = f"CREATE TABLE {nombre_tabla} ({columnas_string});"
            # Se ejecuta la instrucción
            self.cursor.execute(sql)
            # Se hace efectiva
            self.conector.commit()
            # Se informa de que la creación se ha efectuado correctamente.
            print("Se creó la tabla correctamente.")
        except Exception as e:
            print("Ocurrió un error al intentar crear la tabla.")
            print(e)

    # Consultas SQL
    @conexion
    def consulta(self, sql) -> list:
        try:
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as e:
            print("Ocurrió un error. Revisa la instrucción SQL.")
            print(e)
            return []
    
    @conexion
    def insert_course(self, tupla_curso: tuple[CourseDTO, list[SectionDTO]]):
        course, sections = tupla_curso
        try:
            self.conector.start_transaction()
            course_id = self.insertar_registro(c.TABLA_CURSOS, [course])[-1]
            course[gc.ID] = course_id
            for section in sections:
                section[gc.ID_CURSO] = course_id
            self.insertar_registro(c.TABLA_SECCIONES, sections)
            self.conector.commit()
        except Exception as e:
            print(f"Ocurrió un error al intentar insertar el curso y las secciones:\n {e}")
            self.conector.rollback()

    # Método para insertar registros en una tabla
    def insertar_registro(self, nombre_tabla, registros) -> list[int]:

        if not registros:  # Si la lista está vacía
            print("La lista de registro está vacía.")
            return []

        # Obtener las columnas del primer registro
        columnas = list(registros[0].keys())
        if gc.ID in columnas:
            columnas.remove(gc.ID)
        columnas_string = ", ".join(columnas)

        inserted_ids = []
        
        # Crear una lista de strings de valores para cada registro
        for registro in registros:
            valores = [registro[columna] for columna in columnas]
            valores_string = ", ".join([f"'{valor}'" for valor in valores])

            # Crear la instrucción de inserción
            sql = f"INSERT INTO {nombre_tabla} ({columnas_string}) VALUES ({valores_string})"
            
            # Si hay claves duplicadas, se actualizan los valores
            updates = ", ".join([f"{columna}=VALUES({columna})" for columna in columnas])
            sql += f" ON DUPLICATE KEY UPDATE {updates}"

            try:
                self.cursor.execute(sql)
                self.conector.commit()
                inserted_id = self.cursor.lastrowid
                inserted_ids.append(inserted_id)
            except Exception as e:
                print(
                    f"Ocurrió un error al intentar insertar el registro {registro}:\n {e}"
                )
        return inserted_ids

    @conexion
    def clear(self):
        print("Se borraron todas las tablas.")
        sql = "DELETE FROM cursos"
        self.cursor.execute(sql)
        self.conector.commit()

    def crear_tablas(self):
        self.crear_tabla(c.TABLA_CURSOS, c.COLUMNAS_CURSOS)
        self.crear_tabla(c.TABLA_SECCIONES, c.COLUMNAS_SECCIONES)
    
    def recuperar_cursos(self) -> list[CourseDTO]:
        sql = f"SELECT * FROM {c.TABLA_CURSOS}"
        return self.consulta(sql)
    
    def recuperar_curso(self, sigla: str) -> CourseDTO | None:
        sql = f"SELECT * FROM {c.TABLA_CURSOS} WHERE {gc.SIGLA} = '{sigla}'"
        resultado = self.consulta(sql)
        if resultado:
            return CourseDTO(**resultado[0])
    
    def recuperar_secciones(self, id_curso: int) -> list[SectionDTO]:
        sql = f"SELECT * FROM {c.TABLA_SECCIONES} WHERE {gc.ID_CURSO} = {id_curso}"
        return self.consulta(sql)
    
    def recuperar_ofgs(self, area: str) -> dict[str, tuple[CourseDTO, list[SectionDTO]]]:
        sql = f"SELECT * FROM {c.TABLA_CURSOS} WHERE {gc.AREA} = '{area}'"
        dict_ofgs = {}
        for row in self.consulta(sql):
            secciones = self.recuperar_secciones(row[gc.ID])
            dict_ofgs[row[gc.SIGLA]] = (row, secciones)
        return dict_ofgs


if __name__ == "__main__":
    bd = Database()
