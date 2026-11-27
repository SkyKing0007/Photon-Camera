package com.particlesdevs.photoncamera.settings;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringReader;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

/** Typed, deterministic XML config. No arbitrary preference-file paths or XML entity expansion. */
public final class Iris26999XmlConfig {
    private static final int MAX_BYTES = 8 * 1024 * 1024;
    private Iris26999XmlConfig() {}

    public static String fileName(String input) throws IOException {
        String name = input == null ? "" : input.trim();
        if (name.toLowerCase(java.util.Locale.ROOT).endsWith(".xml")) name = name.substring(0, name.length()-4).trim();
        if (name.isEmpty() || name.startsWith(".") || name.length() > 100 || name.endsWith("."))
            throw new IOException("Enter a valid configuration name");
        for (int i=0; i<name.length(); i++) {
            char ch = name.charAt(i);
            if (Character.isISOControl(ch) || "/\\:*?\"<>|".indexOf(ch) >= 0)
                throw new IOException("Invalid configuration name");
        }
        return name + ".xml";
    }

    public static byte[] encode(Map<String, ? extends Map<String, ?>> stores) throws IOException {
        StringBuilder out = new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<iris-config version=\"1\">\n");
        for (Map.Entry<String, ? extends Map<String, ?>> store : new TreeMap<>(stores).entrySet()) {
            out.append("  <store name=\"").append(escape(store.getKey())).append("\">\n");
            for (Map.Entry<String, ?> entry : new TreeMap<>(store.getValue()).entrySet())
                appendValue(out, entry.getKey(), entry.getValue());
            out.append("  </store>\n");
        }
        out.append("</iris-config>\n");
        byte[] data = out.toString().getBytes(StandardCharsets.UTF_8);
        if (data.length > MAX_BYTES) throw new IOException("Configuration too large");
        return data;
    }

    private static void appendValue(StringBuilder out, String key, Object value) throws IOException {
        String attr = " name=\"" + escape(key) + "\"";
        if (value instanceof String) {
            out.append("    <string").append(attr).append('>').append(escape((String)value)).append("</string>\n");
        } else if (value instanceof Set<?>) {
            TreeSet<String> sorted = new TreeSet<>();
            for (Object item : (Set<?>)value) {
                if (!(item instanceof String)) throw new IOException("Unsupported string set");
                sorted.add((String)item);
            }
            out.append("    <set").append(attr).append(">\n");
            for (String item : sorted) out.append("      <string>").append(escape(item)).append("</string>\n");
            out.append("    </set>\n");
        } else {
            String tag;
            if (value instanceof Boolean) tag = "boolean";
            else if (value instanceof Integer) tag = "int";
            else if (value instanceof Long) tag = "long";
            else if (value instanceof Float) tag = "float";
            else throw new IOException("Unsupported preference type: " + key);
            out.append("    <").append(tag).append(attr).append(" value=\"").append(value).append("\"/>\n");
        }
    }

    private static String escape(String value) throws IOException {
        StringBuilder out = new StringBuilder();
        for (int i=0; i<value.length();) {
            int cp = value.codePointAt(i); i += Character.charCount(cp);
            switch (cp) {
                case '&': out.append("&amp;"); break;
                case '<': out.append("&lt;"); break;
                case '>': out.append("&gt;"); break;
                case '"': out.append("&quot;"); break;
                case '\r': out.append("&#13;"); break;
                case '\n': out.append("&#10;"); break;
                case '\t': out.append("&#9;"); break;
                default:
                    if (cp < 32 || cp >= 0xd800 && cp <= 0xdfff || cp == 0xfffe || cp == 0xffff)
                        throw new IOException("Preference contains invalid XML character");
                    out.appendCodePoint(cp);
            }
        }
        return out.toString();
    }

    /** Accept our complete multi-store format or a legacy Android SharedPreferences map. */
    public static Map<String, Map<String, Object>> decode(InputStream in, Set<String> allowed) throws Exception {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream();
        byte[] chunk = new byte[8192];
        int n;
        while ((n = in.read(chunk)) != -1) {
            if (buffer.size() + n > MAX_BYTES) throw new IOException("Configuration too large");
            buffer.write(chunk, 0, n);
        }
        // Parse a UTF-8 Reader, not untrusted encoding declarations. Reject DTDs before parsing.
        String xml = StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(buffer.toByteArray())).toString();
        if (xml.startsWith("\ufeff")) xml = xml.substring(1);
        if (xml.indexOf('\0') >= 0 || xml.contains("<!DOCTYPE") || xml.contains("<!ENTITY"))
            throw new IOException("XML declarations/entities are not allowed");
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setExpandEntityReferences(false);
        DocumentBuilder builder = factory.newDocumentBuilder();
        builder.setEntityResolver((publicId, systemId) -> { throw new SAXException("External entities are not allowed"); });
        Element root = builder.parse(new InputSource(new StringReader(xml))).getDocumentElement();
        Map<String, Map<String, Object>> result = new LinkedHashMap<>();
        if ("map".equals(root.getTagName())) {
            if (!allowed.contains("main")) throw new IOException("Main preferences unavailable");
            result.put("main", readMap(root));
        } else {
            if (!"iris-config".equals(root.getTagName()) || !"1".equals(root.getAttribute("version")))
                throw new IOException("Unsupported configuration format");
            for (Element store : children(root)) {
                String name = store.getAttribute("name");
                if (!"store".equals(store.getTagName()) || !allowed.contains(name) || result.containsKey(name))
                    throw new IOException("Invalid preference store: " + name);
                result.put(name, readMap(store));
            }
            if (!result.keySet().equals(allowed)) throw new IOException("Incomplete configuration");
        }
        return result;
    }

    private static Map<String, Object> readMap(Element root) throws IOException {
        Map<String, Object> map = new LinkedHashMap<>();
        for (Element e : children(root)) {
            if (!e.hasAttribute("name")) throw new IOException("Missing preference name");
            String key = e.getAttribute("name");
            if (key.isEmpty() || map.containsKey(key)) throw new IOException("Duplicate or empty preference name");
            Object value;
            String raw = e.getAttribute("value");
            try {
                switch (e.getTagName()) {
                    case "string": value = textOnly(e); break;
                    case "boolean":
                        if (!"true".equals(raw) && !"false".equals(raw)) throw new IOException("Invalid boolean");
                        value = Boolean.valueOf(raw); break;
                    case "int": value = Integer.valueOf(raw); break;
                    case "long": value = Long.valueOf(raw); break;
                    case "float": value = Float.valueOf(raw); break;
                    case "set":
                        Set<String> set = new LinkedHashSet<>();
                        for (Element member : children(e)) {
                            if (!"string".equals(member.getTagName()) || !set.add(textOnly(member)))
                                throw new IOException("Invalid string set");
                        }
                        value = set; break;
                    default: throw new IOException("Unsupported preference type");
                }
                if (!"string".equals(e.getTagName()) && !"set".equals(e.getTagName()) && !children(e).isEmpty())
                    throw new IOException("Invalid scalar value");
            } catch (NumberFormatException error) { throw new IOException("Invalid numeric preference", error); }
            map.put(key, value);
        }
        return map;
    }

    private static List<Element> children(Element parent) throws IOException {
        List<Element> result = new ArrayList<>();
        for (Node node=parent.getFirstChild(); node!=null; node=node.getNextSibling()) {
            if (node instanceof Element) result.add((Element)node);
            else if (node.getNodeType() != Node.COMMENT_NODE &&
                    (node.getNodeType() != Node.TEXT_NODE || !node.getNodeValue().trim().isEmpty()))
                throw new IOException("Unexpected XML content");
        }
        return result;
    }

    private static String textOnly(Element e) throws IOException {
        for (Node node=e.getFirstChild(); node!=null; node=node.getNextSibling())
            if (node.getNodeType() != Node.TEXT_NODE && node.getNodeType() != Node.CDATA_SECTION_NODE)
                throw new IOException("Invalid string value");
        return e.getTextContent();
    }
}
