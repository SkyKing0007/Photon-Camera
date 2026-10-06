package com.particlesdevs.photoncamera.debugclient;

import com.particlesdevs.photoncamera.util.SimpleStorageHelper;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.IOException;

public class Debugger {
    public DebugClient debugClient;
    public Debugger(){
        String[] ipPort = readDebugClientFile();
        if (ipPort ==null){
            return;
        }
        makeDebugClient(ipPort[0],ipPort[1]);
    }
    private String[] readDebugClientFile(){
        try (InputStream is = SimpleStorageHelper.openIrisInputStream("Tuning/DebugClient.txt")) {
            if (is != null) {
                BufferedReader bufferedReader = new BufferedReader(new InputStreamReader(is));
                String line = bufferedReader.readLine();
                if (line != null) return line.split(":");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    private void makeDebugClient(String ip, String port){
        debugClient = new DebugClient(ip, port);
    }
}
