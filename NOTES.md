# Apuntes de repaso — A-Maze-ing

Notas personales de conceptos de Python que han ido saliendo mientras construíamos
el proyecto. No es parte de la entrega (no lo pide el subject), es solo para repasar
antes de la defensa. Se amplía fichero a fichero conforme avanzamos.

## Dónde lo dejamos (estado actual — 2026-11-21)

**Hecho, con lint limpio (flake8 + mypy normal y `--strict`) y probado a mano:**
- `a_maze_ing.py`: lee `sys.argv`, llama a `load_config`, atrapa `OSError`/
  `ConfigError` por separado + red de seguridad final (`except Exception`).
- `app/config.py`: `Config` (dataclass) + `load_config()` + `ConfigError`.
  Valida claves obligatorias, tipos, rango de ENTRY/EXIT, ENTRY≠EXIT.
- `mazegen/mazegen.py`: `Direction` (IntFlag), `Cell = (fila, col)` interno,
  `MazeGenerator.__init__` (valida, voltea `(x,y)`→`(fila,col)`, crea el grid
  en blanco), `_blank_grid`, `_neighbours`, `_open`, `_carve` (backtracker
  iterativo con pila) y `generate(seed)`. **Solo genera el modo PERFECTO**
  (árbol de expansión, conectividad total, sin bucles) — probado:
  reproducible por seed, coherencia de paredes, nº de pasillos = celdas-1.

**Pendiente (por orden lógico):**
1. Modo no-perfecto (Pac-Man): partir del árbol perfecto y añadir bucles
   controlados + garantizar esquinas/centro abiertos + limitar dead-ends.
2. Patrón "42" (celdas totalmente cerradas) + comprobación de tamaño mínimo.
3. Regla de no-zona-3x3-abierta (en modo perfecto ya es imposible por ser un
   árbol; hay que vigilarla al añadir bucles en el modo no-perfecto).
4. Pathfinding (BFS, camino más corto) — dentro de `mazegen.py`, el subject
   pide que el módulo reutilizable también exponga "al menos una solución".
5. `app/output.py`: escribir el fichero (hex + footer), usando el formato
   `x,y` plano (sin comentarios, pese a lo que sugiere la imagen del subject).
6. `app/display.py`: ASCII + menú interactivo (regenerar, mostrar/ocultar
   camino, cambiar colores).
7. `app/cli.py`: conectar todo; actualizar `a_maze_ing.py` para usarlo.
8. Empaquetar `mazegen` (.whl en la raíz, reconstruible en venv limpio).
9. `README.md` completo + checklist de verificación en el campus.

**Decisiones ya tomadas, no las vuelvas a plantear sin motivo** (detalle
completo en `CLAUDE.md`, raíz del repo): backtracker recursivo (no
Kruskal/Prim); `Cell` interno de `mazegen` es `(fila, col)`, volteo único en
`__init__`; `Config` es un dataclass; `mazegen` nunca importa de `app`.

---

## Arquitectura general del proyecto (resumen)

Analogía: un restaurante.

- `config.txt` = la comanda del cliente (tamaño, entrada/salida, perfecto o no...).
- `a_maze_ing.py` = el camarero: solo coge la comanda (el argumento de terminal) y
  la lleva a cocina. No cocina nada él mismo.
- `app/config.py` = quien lee la comanda y comprueba que tiene sentido (valida
  `config.txt`).
- `mazegen/mazegen.py` = la cocina de verdad: la receta (algoritmo) que construye
  el laberinto y sabe encontrar el camino más corto. Está separada del resto a
  propósito porque el subject exige que sea un módulo **reutilizable e
  instalable con pip**, independiente del resto del proyecto.
- `app/output.py` = emplata el laberinto en el formato exacto que pide el subject
  (fichero de texto con un dígito hex por celda).
- `app/display.py` = el escaparate: dibuja el laberinto en ASCII en terminal y
  lleva el menú interactivo.
- `app/cli.py` = el jefe de cocina: orquesta en qué orden se llama a todo lo
  anterior.

Flujo de una ejecución:
```
usuario → python3 a_maze_ing.py config.txt
        → a_maze_ing.py (coge el argumento)
        → app/cli.py (orquesta)
             ├─ app/config.py     (valida config.txt)
             ├─ mazegen.MazeGenerator  (construye + resuelve)
             ├─ app/output.py    (escribe el fichero de salida)
             └─ app/display.py   (lo dibuja + menú)
```

---

## `a_maze_ing.py`

### `sys.argv`

Lista que Python rellena automáticamente al arrancar, con todo lo que escribiste
en la terminal después de `python3`. El índice `0` es siempre el nombre del propio
script; los siguientes son los argumentos reales del usuario.

```python
# python3 a_maze_ing.py config.txt
sys.argv == ["a_maze_ing.py", "config.txt"]
```

Por eso comprobamos `len(sys.argv)` **antes** de leer `sys.argv[1]` — si el usuario
no pasa ningún argumento, `sys.argv` solo tiene un elemento, y leer el índice `1`
directamente lanzaría un `IndexError` (un crash feo). El subject exige no crashear
nunca y dar siempre un mensaje claro.

### `if __name__ == "__main__":`

Cada módulo de Python tiene una variable automática `__name__`. Vale `"__main__"`
solo cuando el fichero se ejecuta directamente (`python3 a_maze_ing.py`); si en
cambio alguien hiciera `import a_maze_ing` desde otro fichero, `__name__` valdría
`"a_maze_ing"`. El `if` separa "definir cosas" (las funciones) de "ejecutarlas" —
el código de dentro solo corre cuando el fichero es el programa principal, no
cuando se importa.

### `typing` vs `from __future__ import annotations`

Son dos cosas **independientes**, no alternativas una de la otra:

- `typing` es un módulo con nombres reales que importas (`List`, `Dict`,
  `Optional`, `Any`, `Callable`...) — vocabulario para describir tipos.
- `from __future__ import annotations` es un interruptor que cambia *cuándo* se
  evalúa una anotación de tipo: convierte todo lo que pones después de `:` o `->`
  en un string sin evaluar, en vez de ejecutarlo de verdad al definir la función.

```python
def f(x: list) -> int: pass
# SIN el interruptor: f.__annotations__ == {'x': <class 'list'>, 'return': <class 'int'>}
# CON el interruptor: f.__annotations__ == {'x': 'list', 'return': 'int'}
```

Esto importaba sobre todo antes de Python 3.9 (cuando `list[str]` como expresión
real petaba con `TypeError: 'type' object is not subscriptable`) y para
referencias hacia delante (una clase que se referencia a sí misma antes de
terminar de definirse). Como el **suelo del proyecto es Python 3.10** (PEP 585 ya
incluido), `list[str]`, `dict[str, int]`, etc. funcionan de verdad sin necesitar
el interruptor — por eso lo quitamos de `a_maze_ing.py`: no aportaba nada ahí y es
una cosa menos que explicar en la defensa. Se añadirá solo si en otro fichero
aparece una referencia hacia delante real.

Tabla de equivalencias (ya no hace falta `typing` para estas, con suelo 3.10):

| Antes (`typing`) | Ahora (3.10+) |
|---|---|
| `List[str]` | `list[str]` |
| `Dict[str, int]` | `dict[str, int]` |
| `Optional[int]` | `int \| None` |
| `Union[int, str]` | `int \| str` |

`typing` sigue haciendo falta para `Any`, `Callable`, `TypeVar`, `Protocol`,
`TYPE_CHECKING`, `cast`, etc. — cosas sin sintaxis nativa.

### `print(..., file=sys.stderr)` — stdout vs stderr

Un programa tiene dos "tuberías" de salida de texto, ambas objetos de Python que
existen siempre: `sys.stdout` (salida normal) y `sys.stderr` (errores/diagnóstico).
`print()` por defecto escribe en `sys.stdout`; con `file=sys.stderr` le decimos que
escriba por la otra tubería.

Por defecto (sin redirigir nada en la terminal) las dos tuberías acaban en la
misma pantalla — no se nota ninguna diferencia visual. La diferencia aparece solo
si la terminal redirige una por separado:
- `programa > salida.txt` → solo redirige stdout; stderr se sigue viendo en pantalla.
- `programa 2> errores.txt` → solo redirige stderr; stdout se sigue viendo en pantalla.

Se llama `file=` (y no `pipe=` o algo así) porque tanto un fichero real abierto con
`open()` como `sys.stdout`/`sys.stderr` saben hacer `.write(texto)` — para
`print()` los tres son intercambiables.

### `sys.exit(...)`

Termina el proceso de Python y le entrega al sistema operativo un número: el
**código de salida** del proceso (0 = éxito, distinto de 0 = error). Es un canal
totalmente aparte de lo que imprimas por pantalla — herramientas externas
(`Makefile`, CI, la Moulinette) miran ese número para saber si el programa
funcionó, sin tener que leer ni entender ningún texto. Se comprueba en la terminal
con `echo $?` justo después de ejecutar algo.

```python
sys.exit(main())
# 1. se ejecuta main() entero
# 2. main() devuelve un int (0 o 1) con su `return`
# 3. ese int es lo que sys.exit() entrega al sistema operativo
```

Si se te olvida el `sys.exit(...)` y dejas `main()` suelto, el programa sigue
imprimiendo el error igual, pero el proceso siempre termina con código `0`
("todo bien"), aunque en realidad haya fallado.

### Comentarios (`#`) vs docstrings (`"""..."""`)

Python **no tiene** el `/* */` de C — no existe esa sintaxis.

- `#` es un comentario real: el intérprete lo descarta al leer el fichero, no
  existe en tiempo de ejecución.
- `"""..."""` en una posición concreta (primera instrucción de un módulo, función
  o clase) **no es un comentario** — es un string de verdad que Python guarda en
  el atributo especial `__doc__` de esa cosa (`main.__doc__`,
  `a_maze_ing.__doc__`...). Por eso `help()` o el tooltip del editor lo pueden leer:
  sigue "vivo" en memoria.
- Por eso hay dos docstrings en `a_maze_ing.py`: uno documenta el **fichero
  entero** (debajo del shebang, primera línea del módulo) y otro documenta
  **solo `main()`** (primera línea dentro de su `def`). El subject exige
  docstrings PEP 257 en funciones y clases — un `#` no cuenta como eso.
- Comillas triples en vez de comillas normales: permiten texto en varias líneas
  tal cual, sin trucos raros.

---

## `app/config.py`

### Decoradores y `@dataclass`

Un decorador es una función que envuelve a otra función/clase y devuelve una
versión modificada de ella, sin tocar el código original:

```python
@dataclass
class Config:
    ...
# es lo mismo que:
class Config:
    ...
Config = dataclass(Config)
```

`@dataclass` coge una clase que solo tiene **nombres de atributo con su tipo**
(sin métodos) y te genera automáticamente:
- `__init__` (asigna cada atributo a partir de sus anotaciones, en el orden en
  que están escritas).
- `__repr__` (para que `print(config)` salga legible: `Config(width=20, ...)`).
- `__eq__` (para poder comparar dos instancias con `==`).

Importante: **esto no valida nada**. `Config(width="hola", ...)` se dejaría
crear igual en tiempo de ejecución (mypy sí lo marcaría como error en análisis
estático, pero no hay ninguna comprobación mientras el programa corre). Por eso
`Config` es solo "la caja para datos ya buenos" — la validación de verdad (¿es
`WIDTH` un número? ¿existen todas las claves obligatorias?) vive en una función
aparte que lee `config.txt` y, si todo está bien, construye el `Config`.

Los nombres de atributo van en minúscula (`width`, no `WIDTH`) por convención de
Python (PEP 8) para atributos — las mayúsculas (`WIDTH=20`) son solo el formato
de texto del fichero de config; la traducción de uno a otro la hace la función
de carga, no el dataclass.

### `ConfigError` — excepción propia

```python
class ConfigError(Exception):
    """Raised when the configuration file is missing a key or is invalid."""
```
Una clase que hereda de `Exception` y no añade nada más. Sirve para poder hacer
`raise ConfigError("mensaje claro")` en vez de dejar que salte un error genérico
de Python (`ValueError`, `IndexError`...) que no dice nada sobre *qué* parte de
la config está mal. Mismo patrón que `MazeError` en `maze_analyzer.py`.

### `_read_pairs(path)` — leer el fichero con seguridad

```python
def _read_pairs(path: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    with open(path, encoding="utf-8") as config_file:
        for line in config_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise ConfigError(f"invalid line (missing '='): {line!r}")
            key, _, value = line.partition("=")
            pairs[key.strip()] = value.strip()
    return pairs
```

- **`with open(...) as config_file:`** — un *context manager*. Garantiza que el
  fichero se cierra solo al salir del bloque, **incluso si salta una excepción**
  dentro (como nuestro `raise`). Sin `with` habría que acordarse de
  `config_file.close()` a mano, fácil de olvidar si hay un error a mitad. El
  subject pide explícitamente usar context managers para recursos como ficheros.
- **`for line in config_file:`** — un fichero abierto es iterable línea a línea;
  cada `line` incluye el `\n` final hasta que se lo quitamos con `.strip()`.
- **`line.partition("=")`** — divide el string por el **primer** `=`, devolviendo
  siempre 3 trozos: `(antes, "=", después)`. Por eso `key, _, value = ...` — el
  `_` del medio es el propio símbolo `"="`, que no necesitamos, así que se llama
  `_` por convención ("no se usa").
- El `return pairs` está fuera del `for` y del `with`: se ejecuta una sola vez,
  cuando ya se ha leído el fichero entero.

### `{value!r}` en un f-string — `str()` vs `repr()`

`{value}` en un f-string llama por debajo a `str(value)` (versión "bonita para
humanos"). `{value!r}` llama a `repr(value)` (versión "sin ambigüedad, para
depurar" — para un string, entre comillas, con cualquier espacio visible).

```python
valor = "  "
f"recibido {valor}"    # "recibido   "   (¿cuántos espacios hay? no se ve)
f"recibido {valor!r}"  # "recibido '  '" (clarísimo: dos espacios entre comillas)
```
Por eso se usa `!r` en todos los mensajes de `ConfigError`: si el valor que falló
es un string vacío, con espacios de más, o con caracteres raros, el usuario lo ve
exactamente tal cual entre comillas, en vez de un mensaje ambiguo.

### `_parse_int(value, key)` — convertir texto a número con error claro

```python
def _parse_int(value: str, key: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key} must be an integer, got {value!r}") from None
```
- `int("veinte")` lanza un `ValueError` genérico de Python si el texto no es un
  número. Lo atrapamos con `try/except` y lanzamos en su lugar nuestro propio
  `ConfigError`, que sí dice qué clave estaba mal.
- **`raise ... from None`**: sin esto, cuando lanzas una excepción dentro de un
  `except`, Python encadena las dos y muestra ambos tracebacks ("durante el
  manejo del error anterior, ocurrió este otro") — ruidoso para el usuario
  final. `from None` corta esa cadena: solo se ve nuestro `ConfigError`, limpio.

### `_parse_bool(value, key)` — convertir texto a `True`/`False`

```python
def _parse_bool(value: str, key: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ConfigError(f"{key} must be True or False, got {value!r}")
```
- `.lower()` para que `"True"`, `"TRUE"` y `"true"` se traten igual.
- No hay `try/except` aquí porque no existe una función de Python que "intente
  convertir a bool y falle con una excepción concreta" como pasa con `int()` —
  se compara el texto a mano, y si no coincide con nada, error.

### `_parse_coordinates(value, key, width, height)` — "x,y" validado

```python
def _parse_coordinates(value: str, key: str, width: int, height: int) -> tuple[int, int]:
    parts = value.split(",")
    if len(parts) != 2:
        raise ConfigError(f"{key} must be 'x,y', got {value!r}")
    x = _parse_int(parts[0], key)
    y = _parse_int(parts[1], key)
    if not (0 <= x < width and 0 <= y < height):
        raise ConfigError(f"{key} {x},{y} is outside the {width}x{height} maze")
    return x, y
```
- **`value.split(",")`**: corta por cada coma, devuelve una lista. `"0,0,0"` daría
  3 trozos, no 2 — por eso `len(parts) != 2` detecta eso (y el caso "sin coma")
  antes de arriesgarse a un `IndexError` al leer `parts[1]`.
- Reutiliza `_parse_int` para no duplicar la lógica "texto a número, error claro".
- **`0 <= x < width`**: comparaciones encadenadas de Python — equivale a
  `0 <= x and x < width` (en C sería `0 <= x && x < width`, repitiendo `x`).
- **`return x, y`**: sin paréntesis, es lo mismo que `return (x, y)` — Python
  crea la tupla igual, y casa con el tipo `tuple[int, int]` declarado.

### `load_config(path)` — la orquestadora

Llama a todas las funciones anteriores en orden y construye el `Config` final.
No tiene lógica de conversión propia, solo decide en qué orden pedir las cosas.

- **Comprensión de lista** (*list comprehension*):
  ```python
  missing = [key for key in _MANDATORY_KEYS if key not in raw]
  # equivale a:
  missing = []
  for key in _MANDATORY_KEYS:
      if key not in raw:
          missing.append(key)
  ```
  Forma compacta de "recorre esto, quédate con lo que cumpla la condición".
  Comprueba las 6 claves obligatorias de golpe, antes de usar ninguna, para
  poder avisar de **todas** las que faltan a la vez, no solo la primera.
- **`', '.join(missing)`**: lo contrario de `.split(",")` — convierte una lista
  de strings en un único string, pegando cada elemento con `", "` entre medias.
  `["ENTRY", "EXIT"]` → `"ENTRY, EXIT"`.
- Orden importante: `width`/`height` se calculan **antes** que `entry`/`exit`,
  porque `_parse_coordinates` necesita el tamaño del laberinto para comprobar
  que la coordenada cae dentro.
- `Config(width=width, entry=entry, ...)`: argumentos nombrados al construir,
  no posicionales — así queda claro qué valor va a qué campo aunque cambie el
  orden de las líneas de arriba.

---

## `a_maze_ing.py` (conectado a `load_config`)

### Importar nuestro propio paquete

`from app.config import ConfigError, load_config` — funciona porque `app/`
tiene un `__init__.py`, así que Python lo trata como un paquete importable;
`app.config` es el módulo `config.py` de dentro.

### Varios `except` para distintos tipos de fallo

```python
try:
    config = load_config(config_path)
except OSError as error:
    ...
except ConfigError as error:
    ...
```
`load_config` puede fallar por dos motivos distintos: el fichero no se puede
abrir (`OSError`, la lanza `open()` por su cuenta) o el contenido no tiene
sentido (`ConfigError`, la nuestra). Python prueba los `except` en orden y
entra en el primero cuyo tipo coincida — así se puede dar un mensaje distinto
para cada caso.

### `IntFlag` para las paredes — por qué y no un `int` a pelo

```python
from enum import IntFlag

class Direction(IntFlag):
    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8
```
Un `IntFlag` **es** un entero por debajo (mismo rendimiento, mismos bits), pero
con nombre — `Direction.NORTH` en vez de recordar que es el `1`. Soporta los
mismos operadores a nivel de bit que ya conoces de C:
```python
walls = Direction.NORTH | Direction.WEST   # combina flags -> 1 | 8 = 9
bool(walls & Direction.NORTH)               # ¿está puesto ese bit? -> True
```
Encaja 1:1 con el formato de salida del subject (bit0=N, bit1=E, bit2=S,
bit3=W), así que cuando escribamos el fichero de salida no hace falta traducir
nada — el entero ya es el dígito hex. Es el mismo patrón que usa `Direction`
en `maze_analyzer.py`, el script de validación que nos dieron.

---

## `mazegen/mazegen.py` — `MazeGenerator.__init__`

### Entrada/salida y el borde exterior

El subject dice explícitamente: *"As entry and exit are specific cells, there
must be walls at the external borders."* El borde exterior del laberinto se
queda **siempre cerrado del todo**, pase lo que pase con entry/exit — no hace
falta (ni se debe) abrir un hueco hacia fuera aunque entry/exit estén en una
esquina. Son solo las coordenadas donde empieza/acaba el camino a resolver, no
implican ningún agujero en el muro.

### Por qué `MazeGenerator` no recibe un `Config`

Regla de dependencias: `app` puede depender de `mazegen`, `mazegen` **nunca**
puede depender de `app` — si no, el paquete reutilizable (pensado para
instalarse solo, en otro proyecto futuro) arrastraría consigo nuestro formato
de config concreto. Por eso `MazeGenerator` recibe parámetros sueltos
(`width`, `height`, `entry`, `exit`, `perfect`), tipos básicos de Python, no
el dataclass `Config`. La traducción de uno a otro la hará `app/cli.py` más
adelante: `MazeGenerator(width=config.width, entry=config.entry, ...)`.

### `Cell = tuple[int, int]` — alias de tipo

```python
Cell = tuple[int, int]  # (x, y)
```
No es una clase ni un `dataclass`, es solo darle un nombre corto a un tipo que
ya existe, para no repetir `tuple[int, int]` por todos lados en las firmas de
función. Mismo patrón que `Cell = Tuple[int, int]` en `maze_analyzer.py` (ahí
lo usan para `(row, col)`; aquí lo usamos para `(x, y)` — ¡ojo con esa
diferencia de convención entre los dos ficheros!).

### `ValueError` (no `ConfigError`) para validar los parámetros

`__init__` repite validaciones parecidas a las de `load_config` (tamaño
positivo, entry/exit dentro de rango y distintos) — es intencional, no
redundancia de verdad: `MazeGenerator` tiene que defender sus propias reglas
por sí sola, porque un proyecto futuro podría usarlo sin pasar nunca por
nuestro `config.py`. Pero aquí se usa `ValueError`, el tipo genérico de Python
para "este parámetro no tiene sentido" — no `ConfigError`, que es específico
de *nuestro* formato de fichero y no tendría sentido en una librería que no
sabe que existen ficheros de config.

### Índices del grid — `(x, y)` por fuera, `(fila, col)` por dentro (CORREGIDO)

Primer intento: guardar `entry`/`exit` tal cual como `(x, y)` (igual que el
subject y `Config`) pero indexar el grid `grid[y][x]`. Funcionaba, pero
obligaba a "voltear mentalmente" en cada método que tocara el grid
(`_neighbours`, `_open`, y más adelante el pathfinding) — un sitio perfecto
para un bug silencioso que mypy nunca detecta (son dos `int` en una tupla, da
igual el orden para el tipo).

**Por qué `y=0` es la fila de ARRIBA, no la de abajo**: el fichero de salida
se escribe "fila a fila" empezando por la primera línea, y esa primera línea
es la fila superior del laberinto — igual que en un fichero de texto o una
hoja de cálculo, donde la fila 1 está arriba y las filas crecen hacia abajo.
No es el eje Y de un gráfico de matemáticas (donde arriba es "más"). Por eso
ir al Norte (visualmente hacia arriba) significa **restar** a la fila/`y`, no
sumar.

**Arreglo**: dentro de `mazegen.py`, `Cell = (fila, columna)` — el mismo orden
que los índices del grid (`grid[fila][columna]`), así que ya no hace falta
voltear nunca al tocar el grid. El volteo se hace **una sola vez**, al
construir el objeto: `__init__` sigue recibiendo `entry`/`exit` como `(x, y)`
(para no romper cómo lo llama `Config`), pero los guarda ya convertidos:
```python
self.entry: Cell = (entry[1], entry[0])  # (x, y) -> (fila, col)
```
Mismo patrón que `maze_analyzer.py` (su `_parse_coordinate` hace justo este
volteo, una vez, al leer el fichero). El subject permite explícitamente que el
formato interno del módulo reutilizable no coincida con el del fichero de
salida: *"the maze generator module grants access to the maze structure, but
it is not necessarily the same format as the output file."*

### La trampa de `[fila] * n` con listas mutables

```python
fila = [0, 0, 0]
malo = [fila] * 3        # las 3 "filas" son el MISMO objeto en memoria
malo[0][0] = 99          # modifica las 3 a la vez -> [[99,0,0],[99,0,0],[99,0,0]]

bueno = [[0 for _ in range(3)] for _ in range(3)]  # 3 listas independientes
bueno[0][0] = 99          # solo afecta a la fila 0 -> [[99,0,0],[0,0,0],[0,0,0]]
```
`[fila] * 3` no copia la lista, repite la **referencia** al mismo objeto tres
veces. La comprensión anidada, en cambio, vuelve a ejecutar la comprensión
interior en cada vuelta del bucle exterior, creando una lista nueva de verdad
cada vez. Esto importará mucho cuando tallemos pasillos modificando
`grid[y][x]` celda a celda — con la versión con trampa, tallar en una fila
aparecería en todas las demás.

### La red de seguridad final (patrón de `maze_analyzer.py`)

```python
if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:   # última red, no la primera línea de defensa
        print(f"Unexpected error: {error}", file=sys.stderr)
        sys.exit(1)
```
Mismo patrón que usa el script de validación que nos dieron con el subject.
Dentro de `main()` ya se atrapan los errores *esperados* (argumentos, config).
Esta capa de fuera es la red de seguridad para lo que **no** se haya previsto
(un bug propio, algo raro del sistema de ficheros...) — en vez de dejar salir
un traceback, se convierte también en mensaje + código de salida 1, cumpliendo
la regla del subject de "nunca crashear". Por eso aquí sí se captura
`Exception` a secas — en cualquier otro sitio del código, el tipo debe ser lo
más específico posible.
