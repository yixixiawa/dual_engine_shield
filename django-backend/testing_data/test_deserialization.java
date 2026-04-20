import java.io.*;

// Java 漏洞测试

public class VulnerableJavaCode {
    
    // CWE-502: Deserialization of Untrusted Data
    public static Object deserializeData(byte[] data) throws Exception {
        ByteArrayInputStream baos = new ByteArrayInputStream(data);
        ObjectInputStream ois = new ObjectInputStream(baos);
        return ois.readObject();  // 不安全的反序列化
    }
    
    // CWE-89: SQL Injection
    public static void queryUser(String userId, Connection conn) throws SQLException {
        String query = "SELECT * FROM users WHERE id = " + userId;
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(query);  // SQL 注入
    }
    
    // CWE-78: OS Command Injection
    public static void runCommand(String userCmd) throws IOException {
        Runtime.getRuntime().exec("ls " + userCmd);  // 命令注入
    }
    
    // CWE-611: XML External Entity (XXE)
    public static void parseXML(String xmlData) throws Exception {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", true);
        DocumentBuilder builder = factory.newDocumentBuilder();
        Document doc = builder.parse(new InputSource(new StringReader(xmlData)));
    }
}
