from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 j=Path(td)/'crop.jar'
 subprocess.run(['kotlinc',str(R/'app/src/main/java/com/hinnka/mycamera/processor/Iris26986COffDngGeometry.kt'),str(R/'26986_host_fixtures/COffDngGeometryTest.kt'),'-include-runtime','-d',str(j)],check=True)
 subprocess.run(['java','-jar',str(j)],check=True)
