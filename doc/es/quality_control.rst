
==================
Control de calidad
==================

Configuración
=============

Debemos dar de alta los modelos de los documentos que pueden tener tests de 
calidad asociados en nuestra empresa. Para cada uno de ellos elegiremos la 
secuencia que se usará para calcular los números de test.

También debemos elegir la secuencia que usará para calcular los números de las 
muestras.


Preparar tests de calidad
=========================

Un test de calidad es un documento que registra las pruebas realizadas sobre 
otro documento del ERP (un registro) y calcula un resultado final de válido/no 
válido. 

.. important:: Un test por sí sólo no se integra con los procesos del documento 
referenciado, ni condiciona su flujo de trabajo.

Como un mismo tipo de test lo vamos a repetir sobre diferentes registros de un 
mismo documento/modelo, la forma habitual de trabajar será creando una plantilla 
y luego crear el test a partir de la plantilla.

Si en algún momento nos interesa preparar un test puntual sin usar una 
plantilla, el proceso y las pantallas son prácticamente idénticas a crear una 
plantilla pero desde el formulario de test.

Antes de empezar a definir ningún test ni plantilla, debemos definir las 
diferentes pruebas y métodos disponibles (los cuales son reusables por los 
diferentes tests).

--------------------------------
Crear las pruebas para los tests
--------------------------------

Encontramos las diferentes pruebas disponibles en el menú Control de calidad / 
Configuración / Pruebas.
Una prueba puede ser de dos tipos:

* **Cualitativas**: El resultado es un término descriptivo como el color, aroma, 
  etc.
  
* **Cuantitativas**: El resultado es un valor numérico.

Los *métodos* son los diferentes procedimientos disponibles para realizar una 
prueba. Si la prueba es cuantitativa, sólo deberemos introducir su nombre. Si es 
cualitativa añadiremos los posibles valores que puede tomar el test.

---------------
Crear plantilla
---------------

.. inheritref:: quality_control/quality_control:paragraph:plantilla

Una plantilla no es necesario que esté asociada a ningún documento. De estarlo, 
si la plantilla no está integrada con otros procesos (ver apartado específico) 
sólo tiene un valor informativo: saber para qué documento está diseñada dicha 
plantilla.

Una vez elegido un nombre añadimos las líneas del test/plantilla que definen las 
diferentes pruebas a realizar. Las líneas se organizan, por el tipo de prueba, 
entre cualitativas y cuantitativas.

En una línea **cualitativa**, además de definir un nombre para identificarla, 
la *prueba y método* que se va a realizar, se debe elegir el **valor válido** 
de entre los posibles valores de la prueba. Las descripciones se usan como 
información interna y para el informe del test.

En las líneas **cuantitativas**, en vez de definir un valor válido definimos 
una *Unidad* de medida y el **rango de valores válidos** (no el conjunto de 
valores posibles sinó los valores que darán como válido el test).

----------------------------------
Crear un test usando una plantilla
----------------------------------

Creamos los test desde el menú Control de calidad / Tests. Para crear un test 
debemos, necesariamente, elegir sobre qué *documento* se está aplicando.

Elegimos qué *plantilla* queremos usar (no hay ninguna restricción sobre las 
plantillas a elegir) y accionamos el botón *Aplicar plantilla*. Se añadirán al 
test las líneas de la plantilla y se establecerá la *fórmula* y las unidades de 
ésta. El test ya está listo.

-----------------------
Pasar y validar un test
-----------------------

Un test tiene los siguientes estados:

 * Borrador: pendiente de completarse. Hará falta introducir los valores de las 
 pruebas realizadas y confirmarlo.
 * Confirmado: el test ha sido ejecutado por el operario y falta que el 
 supervisor lo valide.
 * Validado: test completado.

Buscamos el test en *borrador* que nos interesa, que debe tener las líneas ya 
definidas, e introducimos los resultados de las diferentes pruebas. Ésto podemos 
hacerlo en el listado mismo de líneas.

En las líneas cuantitativas introduciremos el valor numérico (y si hace falta 
cambiaremos las unidades). Cuando guardemos el sistema calculará el *Resultado 
de la fórmula*.

Cuando ya hemos introducido todos los resultados **confirmamos** el test. Al 
hacerlo el sistema le asignará un *Número* usando la secuencia configurada para 
el tipo de documento asociado.

El campo **válido** será cierto si todas las líneas del test, cuantitativas y 
cualitativas, son válidas, esto es; los valores de las líneas cualitativas son 
todos valores válidos y las de las líneas cuantitativas se encuentran dentro de 
los rangos aceptados para aquel test.

Un test no está finalizado hasta que un responsable lo **valida**. Sólo los 
miembros del grupo *Administración de control de calidad* tienen permisos para 
hacerlo.