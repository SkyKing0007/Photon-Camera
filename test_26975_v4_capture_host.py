#!/usr/bin/env python3
"""V4 independently exercised C-only geometry/flicker/sequence Java + source-path assertions.
No Android runtime, device IQ or original Pro Sabre native merge is implied.
"""
import argparse,pathlib,tempfile,subprocess,base64,hashlib
p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path);a=p.parse_args()
R=pathlib.Path(__file__).resolve().parent
root=a.root or R/'handoff_payload_26975/app'
src=root/'src/main/java'
package='com/particlesdevs/photoncamera/processing/experimentc'
classes=['Iris26975COutputGeometry','Iris26975CDonorExposurePolicy',
         'Iris26975CHighlightFreeze','Iris26975CRawHighlightMeter']
LEGACY_HOST_FIXTURES={'Iris26975CFlickerModeFreeze.java': ('b2cb975989affbca5cc6726dfcf5228714da927adf87b014981a4cf6ebb0c1c5', 'cGFja2FnZSBjb20ucGFydGljbGVzZGV2cy5waG90b25jYW1lcmEucHJvY2Vzc2luZy5leHBlcmltZW50YzsKCi8qKgogKiBFeHBlcmltZW50IEMtb25seSBDYW1lcmEyIGNhcHR1cmUtbWV0YWRhdGEgYWRhcHRlciBmb3IgSXJpcyBmbGlja2VyIHByb3RlY3Rpb24uCiAqIENvcGllcyB0aGUgYWN0dWFsIHBoeXNpY2FsIGNhbWVyYSBhbnRpYmFuZGluZyBzZWxlY3Rpb24gdG8gQy1vd25lZCBSQVcgcmVxdWVzdHM7CiAqIGl0IG5ldmVyIGltcG9ydHMgb3IgcnVucyBFeHBlcmltZW50IEEvQiBwcm9jZXNzaW5nIG9yIHRoZWlyIHJvdy1mbGlja2VyIGZpbHRlcnMuCiAqIFBhc3NpbmcgdGhpcyBzZXR0aW5nIHdoaWxlIEFFIGlzIE9GRiBkb2VzIE5PVCBpdHNlbGYgZXN0YWJsaXNoIHRoYXQgYSBtYW51YWwKICogc2h1dHRlciBpbnRlcnZhbCBpcyBmbGlja2VyLXNhZmU7IHRoYXQgcmVtYWlucyBhIGRpc3RpbmN0IGRldmljZSB0ZXN0IGdhdGUuCiAqLwpwdWJsaWMgZmluYWwgY2xhc3MgSXJpczI2OTc1Q0ZsaWNrZXJNb2RlRnJlZXplIHsKICAgIHByaXZhdGUgSXJpczI2OTc1Q0ZsaWNrZXJNb2RlRnJlZXplKCkge30KCiAgICAvKiogUmV0dXJuIG9ubHkgYSBwaHlzaWNhbCwgYWN0dWFsbHkgc3VwcG9ydGVkIHJlcXVlc3QgdmFsdWU7IG5ldmVyIGludmVudCBBVVRPLiAqLwogICAgcHVibGljIHN0YXRpYyBJbnRlZ2VyIGZyZWV6ZShJbnRlZ2VyIHBoeXNpY2FsT2JzZXJ2ZWQsIEludGVnZXIgaXJpc1ByZXZpZXdSZXF1ZXN0LAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBpbnRbXSBzdXBwb3J0ZWRNb2RlcykgewogICAgICAgIGlmIChzdXBwb3J0ZWRNb2RlcyA9PSBudWxsIHx8IHN1cHBvcnRlZE1vZGVzLmxlbmd0aCA9PSAwKSByZXR1cm4gbnVsbDsKICAgICAgICBpZiAoc3VwcG9ydGVkKHBoeXNpY2FsT2JzZXJ2ZWQsIHN1cHBvcnRlZE1vZGVzKSkgcmV0dXJuIHBoeXNpY2FsT2JzZXJ2ZWQ7CiAgICAgICAgaWYgKHN1cHBvcnRlZChpcmlzUHJldmlld1JlcXVlc3QsIHN1cHBvcnRlZE1vZGVzKSkgcmV0dXJuIGlyaXNQcmV2aWV3UmVxdWVzdDsKICAgICAgICByZXR1cm4gbnVsbDsKICAgIH0KCiAgICBwcml2YXRlIHN0YXRpYyBib29sZWFuIHN1cHBvcnRlZChJbnRlZ2VyIGNhbmRpZGF0ZSwgaW50W10gbW9kZXMpIHsKICAgICAgICBpZiAoY2FuZGlkYXRlID09IG51bGwpIHJldHVybiBmYWxzZTsKICAgICAgICBmb3IgKGludCB2YWx1ZSA6IG1vZGVzKSBpZiAodmFsdWUgPT0gY2FuZGlkYXRlLmludFZhbHVlKCkpIHJldHVybiB0cnVlOwogICAgICAgIHJldHVybiBmYWxzZTsKICAgIH0KfQo='), 'Iris26975CNightExposureFreeze.java': ('c41ba8bca62961de811766207654ee3997e5c717c68091f8b178e379863f6aec', 'cGFja2FnZSBjb20ucGFydGljbGVzZGV2cy5waG90b25jYW1lcmEucHJvY2Vzc2luZy5leHBlcmltZW50YzsKCi8qKgogKiBDLXByaXZhdGUgY2FwdHVyZS1zaWRlIGFkYXB0YXRpb24gb2YgSXJpcyBOaWdodCdzIE5PUk1BTC1vbmx5IGV4cG9zdXJlIHByaW5jaXBsZToKICogZnJlc2ggcG9zdC1zaHV0dGVyIFJBVywgc2h1dHRlci10aW1lIGZyb3plbiBleHBvc3VyZSwgdXAgdG8gMTAwbXMgaW50ZWdyYXRpb24KICogYmVmb3JlIGluY3JlYXNpbmcgSVNPLCBhbmQgYWN0dWFsIHBoeXNpY2FsIENhbWVyYTIgYW50aWJhbmRpbmcgZXZpZGVuY2UuCiAqIEl0IG5ldmVyIGNhbGxzIEEvQiBOaWdodCBwcm9jZXNzaW5nLCByZWNvbnN0cnVjdG9ycywgaW1hZ2UgbWVyZ2luZyBvciBzYXZlIHBhdGhzLgogKgogKiBBL0IgTmlnaHQncyBvcHRpb25hbCBzZXBhcmF0ZSBMT05HIGV4cG9zdXJlIGNvaG9ydCBpcyBpbnRlbnRpb25hbGx5IE5PVCBhcHBsaWVkCiAqIHRvIGRvbm9yIFNhYnJlJ3Mgc2FtZS1leHBvc3VyZSBSQVcgaW5wdXQuIFRoYXQgcmVtYWlucyBhbiBleHBsaWNpdCBpbnRlZ3JhdGlvbgogKiBhbmQgZGV2aWNlLXZlcmlmaWNhdGlvbiByZXF1aXJlbWVudCwgbm90IGEgc2lsZW50bHkgY29lcmNlZCBmcmFtZSByb2xlLgogKi8KcHVibGljIGZpbmFsIGNsYXNzIElyaXMyNjk3NUNOaWdodEV4cG9zdXJlRnJlZXplIHsKICAgIHByaXZhdGUgc3RhdGljIGZpbmFsIGxvbmcgTklHSFRfTk9STUFMX1NIVVRURVJfQ0VJTElOR19OUyA9IDEwMF8wMDBfMDAwTDsKICAgIHB1YmxpYyBzdGF0aWMgZmluYWwgaW50IEhBTF9BTlRJQkFORElOR181MEhaID0gMTsKICAgIHB1YmxpYyBzdGF0aWMgZmluYWwgaW50IEhBTF9BTlRJQkFORElOR182MEhaID0gMjsKCiAgICBwdWJsaWMgc3RhdGljIGZpbmFsIGNsYXNzIFBsYW4gewogICAgICAgIHB1YmxpYyBmaW5hbCBsb25nIGV4cG9zdXJlTnM7CiAgICAgICAgcHVibGljIGZpbmFsIGludCBpc287CiAgICAgICAgcHVibGljIGZpbmFsIGJvb2xlYW4gdXNlck1hbnVhbDsKICAgICAgICBwcml2YXRlIFBsYW4obG9uZyBleHBvc3VyZU5zLCBpbnQgaXNvLCBib29sZWFuIHVzZXJNYW51YWwpIHsKICAgICAgICAgICAgdGhpcy5leHBvc3VyZU5zID0gZXhwb3N1cmVOczsKICAgICAgICAgICAgdGhpcy5pc28gPSBpc287CiAgICAgICAgICAgIHRoaXMudXNlck1hbnVhbCA9IHVzZXJNYW51YWw7CiAgICAgICAgfQogICAgfQoKICAgIHByaXZhdGUgSXJpczI2OTc1Q05pZ2h0RXhwb3N1cmVGcmVlemUoKSB7fQoKICAgIC8qKiBDb3B5IG9mIHRoZSBJcmlzIE5pZ2h0IE5PUk1BTC1vbmx5IHNodXR0ZXItcHJpb3JpdHkgYXJpdGhtZXRpYywgQy1vd25lZC4gKi8KICAgIHB1YmxpYyBzdGF0aWMgUGxhbiBmcmVlemUoYm9vbGVhbiB1c2VyTWFudWFsLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBsb25nIGZyb3plbklyaXNFeHBvc3VyZU5zLCBpbnQgZnJvemVuSXJpc0lzbywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgbG9uZyBzZW5zb3JFeHBvc3VyZUxvd05zLCBsb25nIHNlbnNvckV4cG9zdXJlSGlnaE5zLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICBpbnQgc2Vuc29ySXNvTG93LCBpbnQgc2Vuc29ySXNvSGlnaCwKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgZG91YmxlIGV4cG9zdXJlQ29tcGVuc2F0aW9uRXYsCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIEludGVnZXIgZnJvemVuUGh5c2ljYWxBbnRpYmFuZGluZywKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgYm9vbGVhbiBpcmlzSGlnaGxpZ2h0UHJvdGVjdGlvbkFjdGl2ZSkgewogICAgICAgIGlmIChmcm96ZW5JcmlzRXhwb3N1cmVOcyA8PSAwTCB8fCBmcm96ZW5JcmlzSXNvIDw9IDAgfHwKICAgICAgICAgICAgICAgIHNlbnNvckV4cG9zdXJlTG93TnMgPD0gMEwgfHwgc2Vuc29yRXhwb3N1cmVIaWdoTnMgPCBzZW5zb3JFeHBvc3VyZUxvd05zIHx8CiAgICAgICAgICAgICAgICBzZW5zb3JJc29Mb3cgPD0gMCB8fCBzZW5zb3JJc29IaWdoIDwgc2Vuc29ySXNvTG93IHx8CiAgICAgICAgICAgICAgICBmcm96ZW5JcmlzRXhwb3N1cmVOcyA8IHNlbnNvckV4cG9zdXJlTG93TnMgfHwKICAgICAgICAgICAgICAgIGZyb3plbklyaXNFeHBvc3VyZU5zID4gc2Vuc29yRXhwb3N1cmVIaWdoTnMgfHwKICAgICAgICAgICAgICAgIGZyb3plbklyaXNJc28gPCBzZW5zb3JJc29Mb3cgfHwgZnJvemVuSXJpc0lzbyA+IHNlbnNvcklzb0hpZ2ggfHwKICAgICAgICAgICAgICAgICFEb3VibGUuaXNGaW5pdGUoZXhwb3N1cmVDb21wZW5zYXRpb25FdikgfHwKICAgICAgICAgICAgICAgIE1hdGguYWJzKGV4cG9zdXJlQ29tcGVuc2F0aW9uRXYpID4gMTAuMCkgewogICAgICAgICAgICB0aHJvdyBuZXcgSWxsZWdhbEFyZ3VtZW50RXhjZXB0aW9uKCJDIE5pZ2h0IHJlcXVpcmVzIGEgdmFsaWQgZnJvemVuIHBoeXNpY2FsIElyaXMgZXhwb3N1cmUiKTsKICAgICAgICB9CiAgICAgICAgaWYgKHVzZXJNYW51YWwpIHJldHVybiBuZXcgUGxhbihmcm96ZW5JcmlzRXhwb3N1cmVOcywgZnJvemVuSXJpc0lzbywgdHJ1ZSk7CiAgICAgICAgbG9uZyBjYXAgPSBNYXRoLm1pbihzZW5zb3JFeHBvc3VyZUhpZ2hOcywgTklHSFRfTk9STUFMX1NIVVRURVJfQ0VJTElOR19OUyk7CiAgICAgICAgaWYgKGNhcCA8IHNlbnNvckV4cG9zdXJlTG93TnMpCiAgICAgICAgICAgIHRocm93IG5ldyBJbGxlZ2FsQXJndW1lbnRFeGNlcHRpb24oIkMgTmlnaHQgaGFzIG5vIHBlcm1pc3NpYmxlIGV4cG9zdXJlIGludGVydmFsIik7CiAgICAgICAgZG91YmxlIG9yaWdpbmFsRW5lcmd5ID0gZnJvemVuSXJpc0V4cG9zdXJlTnMgKiAoZG91YmxlKSBmcm96ZW5JcmlzSXNvOwogICAgICAgIGRvdWJsZSB0YXJnZXRFbmVyZ3kgPSBvcmlnaW5hbEVuZXJneSAqIE1hdGgucG93KDIuMCwgZXhwb3N1cmVDb21wZW5zYXRpb25Fdik7CiAgICAgICAgaWYgKGlyaXNIaWdobGlnaHRQcm90ZWN0aW9uQWN0aXZlKSB7CiAgICAgICAgICAgIC8vIEEgZnJlc2ggTmlnaHQgY2FwdHVyZSBtYXkgbW92ZSBpbnRlZ3JhdGlvbiB0aW1lL0lTTywgYnV0IG5ldmVyIGRlZmVhdAogICAgICAgICAgICAvLyBhbiBhbHJlYWR5LWZyb3plbiBJcmlzIGhpZ2hsaWdodC1wcm90ZWN0aW9uIGV4cG9zdXJlIGJ1ZGdldC4KICAgICAgICAgICAgdGFyZ2V0RW5lcmd5ID0gTWF0aC5taW4odGFyZ2V0RW5lcmd5LCBvcmlnaW5hbEVuZXJneSk7CiAgICAgICAgfQogICAgICAgIGlmICghKHRhcmdldEVuZXJneSA+IDAuMCkgfHwgIURvdWJsZS5pc0Zpbml0ZSh0YXJnZXRFbmVyZ3kpKQogICAgICAgICAgICB0aHJvdyBuZXcgSWxsZWdhbEFyZ3VtZW50RXhjZXB0aW9uKCJDIE5pZ2h0IHRhcmdldCBlbmVyZ3kgaW52YWxpZCIpOwogICAgICAgIGxvbmcgZGVzaXJlZCA9IE1hdGgucm91bmQodGFyZ2V0RW5lcmd5IC8gTWF0aC5tYXgoMS4wLCBzZW5zb3JJc29Mb3cpKTsKICAgICAgICBsb25nIHNodXR0ZXIgPSBjbGFtcChkZXNpcmVkLCBzZW5zb3JFeHBvc3VyZUxvd05zLCBjYXApOwogICAgICAgIC8vIFByZXNlcnZlcyBJcmlzIE5pZ2h0J3MgNTAvNjBIeiBpbnRlZ3JhdGlvbiBwZXJpb2RzIHdoZW4gdGhlIHBoeXNpY2FsCiAgICAgICAgLy8gY2FtZXJhIGFjdHVhbGx5IGlkZW50aWZpZXMgb25lLiBOZXZlciBpbnZlbnQgYSA2MEh6IHBlcmlvZCBmb3IgQVVUTy4KICAgICAgICBsb25nIHBlcmlvZCA9IGZyb3plblBoeXNpY2FsQW50aWJhbmRpbmcgIT0gbnVsbCAmJgogICAgICAgICAgICAgICAgZnJvemVuUGh5c2ljYWxBbnRpYmFuZGluZyA9PSBIQUxfQU5USUJBTkRJTkdfNTBIWiA/IDEwXzAwMF8wMDBMIDoKICAgICAgICAgICAgICAgIGZyb3plblBoeXNpY2FsQW50aWJhbmRpbmcgIT0gbnVsbCAmJgogICAgICAgICAgICAgICAgZnJvemVuUGh5c2ljYWxBbnRpYmFuZGluZyA9PSBIQUxfQU5USUJBTkRJTkdfNjBIWiA/IDhfMzMzXzMzM0wgOiAwTDsKICAgICAgICBpZiAocGVyaW9kID4gMCAmJiBzaHV0dGVyID49IHBlcmlvZCkgewogICAgICAgICAgICBsb25nIG4gPSBNYXRoLm1heCgxTCwgTWF0aC5yb3VuZCgoZG91YmxlKSBzaHV0dGVyIC8gcGVyaW9kKSk7CiAgICAgICAgICAgIHdoaWxlIChuICogcGVyaW9kID4gY2FwICYmIG4gPiAxTCkgbi0tOwogICAgICAgICAgICBzaHV0dGVyID0gY2xhbXAobiAqIHBlcmlvZCwgc2Vuc29yRXhwb3N1cmVMb3dOcywgY2FwKTsKICAgICAgICB9CiAgICAgICAgaW50IGlzbyA9IChpbnQpIE1hdGgubWF4KHNlbnNvcklzb0xvdywKICAgICAgICAgICAgICAgIE1hdGgubWluKHNlbnNvcklzb0hpZ2gsIE1hdGgucm91bmQodGFyZ2V0RW5lcmd5IC8gc2h1dHRlcikpKTsKICAgICAgICBpZiAoaXJpc0hpZ2hsaWdodFByb3RlY3Rpb25BY3RpdmUgJiYKICAgICAgICAgICAgICAgIHNodXR0ZXIgKiAoZG91YmxlKSBpc28gPiBvcmlnaW5hbEVuZXJneSkgewogICAgICAgICAgICAvLyBBbnRpYmFuZGluZyByb3VuZGluZyBtdXN0IG5vdCB1bmRvIHBoeXNpY2FsIGhpZ2hsaWdodCBwcm90ZWN0aW9uLgogICAgICAgICAgICAvLyBQcmVmZXIgYSBzaG9ydGVyIGNvbXBsZXRlIG1haW5zIHBlcmlvZCBvdmVyIGluY3JlYXNpbmcgcGhvdG9ucy4KICAgICAgICAgICAgbG9uZyBzYWZlRXhwb3N1cmUgPSAobG9uZykgTWF0aC5mbG9vcihvcmlnaW5hbEVuZXJneSAvIHNlbnNvcklzb0xvdyk7CiAgICAgICAgICAgIGlmIChwZXJpb2QgPiAwTCAmJiBzYWZlRXhwb3N1cmUgPj0gcGVyaW9kKSB7CiAgICAgICAgICAgICAgICBsb25nIHNhZmVQZXJpb2RzID0gTWF0aC5tYXgoMUwsIHNhZmVFeHBvc3VyZSAvIHBlcmlvZCk7CiAgICAgICAgICAgICAgICBzaHV0dGVyID0gTWF0aC5taW4oc2h1dHRlciwgc2FmZVBlcmlvZHMgKiBwZXJpb2QpOwogICAgICAgICAgICB9IGVsc2UgewogICAgICAgICAgICAgICAgc2h1dHRlciA9IE1hdGgubWluKHNodXR0ZXIsIHNhZmVFeHBvc3VyZSk7CiAgICAgICAgICAgIH0KICAgICAgICAgICAgaWYgKHNodXR0ZXIgPCBzZW5zb3JFeHBvc3VyZUxvd05zKSB7CiAgICAgICAgICAgICAgICB0aHJvdyBuZXcgSWxsZWdhbEFyZ3VtZW50RXhjZXB0aW9uKAogICAgICAgICAgICAgICAgICAgICAgICAiQyBOaWdodCBjYW5ub3QgcHJlc2VydmUgdGhlIGZyb3plbiBoaWdobGlnaHQgZW5lcmd5IGJ1ZGdldCIpOwogICAgICAgICAgICB9CiAgICAgICAgICAgIGlzbyA9IChpbnQpIE1hdGgubWF4KHNlbnNvcklzb0xvdywgTWF0aC5taW4oc2Vuc29ySXNvSGlnaCwKICAgICAgICAgICAgICAgICAgICAobG9uZykgTWF0aC5mbG9vcihvcmlnaW5hbEVuZXJneSAvIHNodXR0ZXIpKSk7CiAgICAgICAgICAgIGlmIChzaHV0dGVyICogKGRvdWJsZSkgaXNvID4gb3JpZ2luYWxFbmVyZ3kpIHsKICAgICAgICAgICAgICAgIHRocm93IG5ldyBJbGxlZ2FsQXJndW1lbnRFeGNlcHRpb24oCiAgICAgICAgICAgICAgICAgICAgICAgICJDIE5pZ2h0IGhpZ2hsaWdodGVkIHNvdXJjZSBjYW5ub3QgaG9ub3IgcGh5c2ljYWwgc2Vuc29yIGJvdW5kcyIpOwogICAgICAgICAgICB9CiAgICAgICAgfQogICAgICAgIHJldHVybiBuZXcgUGxhbihzaHV0dGVyLCBpc28sIGZhbHNlKTsKICAgIH0KCiAgICBwcml2YXRlIHN0YXRpYyBsb25nIGNsYW1wKGxvbmcgdmFsdWUsIGxvbmcgbG93LCBsb25nIGhpZ2gpIHsKICAgICAgICByZXR1cm4gTWF0aC5tYXgobG93LCBNYXRoLm1pbihoaWdoLCB2YWx1ZSkpOwogICAgfQp9Cg==')}
paths=[src/package/(name+'.java') for name in classes]
fencePath=src/package/'Iris26972CSequenceFence.java'
withFence=fencePath.is_file()
if withFence:paths.append(fencePath)
for path in paths:assert path.is_file(),str(path)
controller=(src/'com/particlesdevs/photoncamera/capture/CaptureController.java').read_text()
cap=(src/'com/hinnka/mycamera/processor/Iris26972CCamera2ShutterSession.kt').read_text()
bridge=(src/'com/hinnka/mycamera/processor/Iris26972CCaptureToGallery.kt').read_text()
donor=(src/'com/hinnka/mycamera/processor/experimentc/Iris26975CPinnedDonorProEngine.kt').read_text()
for token in ('mIris26975CZslRingBuffer','mIris26975CZslResultMap',
              'mIris26975CZslPreviewSelected','IRIS_26975_V4_C_PRIVATE_ZSL_INGRESS',
              'Math.min(frames,','IRIS_26975_V4_C_ALL_PRE_SHUTTER',
              'mIris26975CFactoryPreviewAntibanding',
              'owner.activate()'):
 assert token in controller,token
assert 'Math.min(Math.min(frames - 1, 8)' not in controller
assert 'preShutterImages.size <= frameCount' in cap
assert 'private var activated = false' in cap and 'if (!activated) return' in cap
for token in ('val geometry:','plan.geometry,','output.geometry.outputWidth'):
 assert token in bridge,token
for token in ('val shutterCrop = Rect(shutterGrid.cropLeft,','defaultCrop = Rect(shutterCrop)',
              'rawPhysicalOutputSize = Size(shutterGrid.rawWidth, shutterGrid.rawHeight)',
              'RawRenderingEngine.AdobeCurve','MultiFrameStacker.processBurstRaw',
              'renderer.processMgcSpatialGpuLinearRgb'):
 assert token in donor,token
assert 'rawPhysicalOutputSize = Size(output.finalWidth, output.finalHeight)' not in donor
# C capture evidence and always-on JPEG/R. Require actual physical match at both ingress and render.
assert 'getTargets()' not in controller
assert 'request == mIris26975CProvenRawPreviewRequest' in controller
assert 'mIris26974PreviewTargetOwner == builder && mIris26974PreviewRawTargetAdded' in controller
assert 'if (isZslMode() && !iris26975CSelectedForMotion())' in controller
assert 'iris26975CMeterOwnRawAtShutter' in controller and 'Iris26975CHighlightFreeze.freezeOwnMeter' in controller
body=controller.split('private void iris26972CStartIndependentCamera2(boolean night) {',1)[1].split('final int[] caps = cPhysicalCharacteristics',1)[0]
assert 'mMotion' not in body and 'lastMotionExposureDiagnostics' not in body
assert 'Iris26975CDonorExposurePolicy.freeze' in controller and 'Iris26975CDonorExposurePolicy.allowHighlightAdjustment' in controller
assert 'Iris26975CFlickerModeFreeze' not in controller and 'Iris26975CNightExposureFreeze' not in controller
assert 'validateNonBlackBase(checkNotNull(sdr), reference, shutterGrid)' in donor
assert 'PROCESSING_DEADLINE_MS' in cap
for name in LEGACY_HOST_FIXTURES: assert not (src/package/name).exists()
assert 'reference.physicalCaptureResult' in donor and 'includeHdrReference = true' in donor
assert 'Jpeg444ExportEncoder.isJpegR(temporary)' in donor and 'Original JPEG/R gainmap unavailable' in donor
contract=(src/package/'Iris26972CContract.java').read_text()
assert 'ULTRA_HDR_ENABLED = true' in contract
burst=(src/'com/hinnka/mycamera/processor/experimentc/Iris26975COriginalRawBurst.kt').read_text()
assert 'meta.exposureTimeNs == ref.metadata.exposureTimeNs' in burst and 'meta.sensitivityIso == ref.metadata.sensitivityIso' in burst
assert 'frame.physicalCaptureResult.get(CaptureResult.SENSOR_TIMESTAMP) == meta.sensorTimestampNs' in burst

java='''import com.particlesdevs.photoncamera.processing.experimentc.*;
public final class V4GeometryAndFlickerHost {
  static void verify(boolean v) { if (!v) throw new AssertionError("V4 host"); }
  static void approx(double a,double b) { verify(Math.abs(a-b)<1.0); }
  public static void main(String[] args) {
    for (int r: new int[]{0,90,180,270}) {
      boolean q=r==90||r==270;
      Iris26975COutputGeometry g=new Iris26975COutputGeometry(4000,3000,
          400,300,3600,2700,r,q?3000:4000,q?4000:3000);
      verify(g.outputWidth==(q?3000:4000));
      verify(g.outputHeight==(q?4000:3000));
      double[] center=g.sourcePixelCenter(g.outputWidth/2,g.outputHeight/2);
      approx(center[0],2000);approx(center[1],1500);
      int[] halo=g.sourceFootprint(0,0,g.outputWidth,g.outputHeight);
      verify(halo[0]>=0 && halo[1]>=0 && halo[2]<=4000 && halo[3]<=3000);
      verify(!g.isExactNativePixelGrid());
    }
    Iris26975COutputGeometry nativeGrid=new Iris26975COutputGeometry(4000,3000,
        0,0,4000,3000,90,3000,4000);
    verify(nativeGrid.isExactNativePixelGrid());
    verify(Iris26975CFlickerModeFreeze.freeze(3,1,new int[]{0,1,2,3})==3);
    verify(Iris26975CFlickerModeFreeze.freeze(9,2,new int[]{1,2})==2);
    verify(Iris26975CFlickerModeFreeze.freeze(null,null,new int[]{0,1})==null);
    /* OPTIONAL_SEQUENCE_FENCE_TEST */
    Iris26975CHighlightFreeze.Decision manual=Iris26975CHighlightFreeze.freeze(
      true,10000000,100,100000L,1,true,1,100000L,300000000d,-1.5f,
      100000,100000000L,50,6400);
    verify(manual.exposureNs==10000000&&manual.iso==100);
    java.nio.ByteBuffer raw=java.nio.ByteBuffer.allocate(320*120+8).order(java.nio.ByteOrder.nativeOrder());
    raw.position(8); float[] black={64,64,64,64};
    for(int y=0;y<120;y++)for(int x=0;x<144;x++)raw.putShort(8+y*320+x*2,(short)100);
    verify(Iris26975CRawHighlightMeter.protectionEv(raw,320,2,0,0,144,120,1023,black)==0f);
    for(int y=0;y<120;y++)for(int x=0;x<144;x++)raw.putShort(8+y*320+x*2,(short)(x>=112?1023:160));
    float ev=Iris26975CRawHighlightMeter.protectionEv(raw,320,2,0,0,144,120,1023,black);
    verify(ev>=.35f && ev<=1.5f && raw.position()==8);
    boolean invalid=false;try{Iris26975CRawHighlightMeter.protectionEv(raw,200,2,0,0,144,120,1023,black);}catch(IllegalArgumentException ex){invalid=true;}verify(invalid);
    Iris26975CHighlightFreeze.Decision privateMeter=Iris26975CHighlightFreeze.freezeOwnMeter(false,10000000,100,ev,100000,100000000L,50,6400);
    verify(privateMeter.exposureNs<10000000 && privateMeter.iso==100 && privateMeter.authority.equals("C_PRIVATE_RAW_METER"));
    Iris26975CHighlightFreeze.Decision noEvidence=Iris26975CHighlightFreeze.freezeOwnMeter(false,10000000,100,Float.NaN,100000,100000000L,50,6400);
    verify(noEvidence.exposureNs==10000000 && noEvidence.iso==100);
    Iris26975CHighlightFreeze.Decision manualMeter=Iris26975CHighlightFreeze.freezeOwnMeter(true,10000000,100,ev,100000,100000000L,50,6400);
    verify(manualMeter.exposureNs==10000000 && manualMeter.iso==100);
    Iris26975CDonorExposurePolicy.Pair auto=Iris26975CDonorExposurePolicy.freeze(0,0,8333333L,640,10000000L,100,100000,1000000000L,50,6400,1000000000L);
    verify(auto.shutterNs==8333333L && auto.iso==640);
    Iris26975CDonorExposurePolicy.Pair hz50=Iris26975CDonorExposurePolicy.freeze(0,0,10000000L,200,8333333L,400,100000,1000000000L,50,6400,null);
    verify(hz50.shutterNs==10000000L && hz50.iso==200);
    Iris26975CDonorExposurePolicy.Pair still=Iris26975CDonorExposurePolicy.freeze(250000000,800,66666666L,100,66666666L,800,100000,1000000000L,50,6400,1000000000L);
    verify(still.shutterNs==250000000L && still.iso==800);
    verify(Iris26975CDonorExposurePolicy.allowHighlightAdjustment(3,0));
    verify(!Iris26975CDonorExposurePolicy.allowHighlightAdjustment(0,1));
    verify(!Iris26975CDonorExposurePolicy.allowHighlightAdjustment(3,null));
    verify(!Iris26975CDonorExposurePolicy.allowHighlightAdjustment(null,null));
    verify(Iris26975CDonorExposurePolicy.allowHighlightAdjustment(0,null));
    boolean bad=false;try{Iris26975CDonorExposurePolicy.freeze(0,0,null,200,10000000L,200,100000,1000000000L,50,6400,null);}catch(IllegalArgumentException ex){bad=true;}verify(bad);
    verify(Iris26975CRawHighlightMeter.measure(raw,320,2,0,0,144,120,1023,black).mean > .08f);
    System.out.println("PASS V14 donor exact metered pair, full explicit still shutter, highlight compatibility, missing metadata rejection");
    System.out.println("PASS V13 C private RAW meter dark/clipping/stride/no-evidence/manual, exact physical source and mandatory JPEG/R source gates");
    System.out.println("PASS V4 C-owned crop/rotation 4x, Lanczos footprint, HAL flicker selection, full-ZSL fence, manual priority");
  }
}
'''
if withFence:
 java=java.replace('/* OPTIONAL_SEQUENCE_FENCE_TEST */','''
    Iris26972CSequenceFence f=new Iris26972CSequenceFence();
    verify(!f.takeReleasePermit());f.markNeverSubmitted();verify(!f.takeReleasePermit());
    f.markTerminalDelivered();verify(f.takeReleasePermit());verify(!f.takeReleasePermit());
    Iris26972CSequenceFence posted=new Iris26972CSequenceFence();
    posted.markTerminalDelivered();verify(!posted.takeReleasePermit());
    posted.markCameraSequenceEnded();verify(posted.takeReleasePermit());
''' )
with tempfile.TemporaryDirectory(prefix='photon_26975_v4_java_') as d:
 d=pathlib.Path(d);(d/'V4GeometryAndFlickerHost.java').write_text(java)
 for name,(h,encoded) in LEGACY_HOST_FIXTURES.items():
  raw=base64.b64decode(encoded);assert hashlib.sha256(raw).hexdigest()==h
  fixture=d/name;fixture.write_bytes(raw);paths.append(fixture)
 subprocess.run(['javac','-d',str(d),*[str(x) for x in paths],str(d/'V4GeometryAndFlickerHost.java')],check=True)
 subprocess.run(['java','-cp',str(d),'V4GeometryAndFlickerHost'],check=True)
print('PASS V4 actual C source ownership/isolation/physical renderer geometry static assertions')
