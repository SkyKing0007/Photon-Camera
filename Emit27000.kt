import java.io.File
import com.hinnka.mycamera.processor.experimentc.original129.processor.GlesGraphicsShaderSources
fun main(args:Array<String>){
 val output=File(args[0]);output.mkdirs();val root="com.hinnka.mycamera.processor.experimentc.original129."
 var count=0
 for(name in args.drop(1)){
  val cls=Class.forName(root+name);val obj=cls.getDeclaredField("INSTANCE").get(null)
  for(method in cls.declaredMethods.sortedBy{it.name}) {
   if(method.parameterCount!=0||method.returnType!=String::class.java||!java.lang.reflect.Modifier.isPublic(method.modifiers))continue
   val src=(method.invoke(obj) as String).trim()
   if(!src.startsWith("#version")||!src.contains(Regex("\\bvoid\\s+main\\s*\\(")))continue
   val stage=if(src.contains("gl_GlobalInvocationID")||src.contains("local_size_"))"comp" else if(src.contains("gl_Position"))"vert" else "frag"
   val base=name.substringAfterLast('.')+"__"+method.name
   File(output,"$base.$stage").writeText(src+"\n");count++
   if(stage=="frag")File(output,"$base.vert").writeText(GlesGraphicsShaderSources.fullscreenVertexFor(src)+"\n")
  }
 }
 check(count>0);println("PASS Kotlin-compiled actual shader getters: $count source programs")
}
