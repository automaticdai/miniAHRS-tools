//  Title    : miniAHRS 3D display 
//  Author   : YunFei
//  Date     : 22/08/2011
//  Changlog : N/A
//  This code is based on '3D Box rotation' by 'Michael Hawthorne'

import processing.opengl.*;
import processing.net.*;

Server myServer;

int roll, pitch, yaw = 0;


void setup(){
  size(200, 200, OPENGL);
  //smooth();
  myServer = new Server(this, 8888);

}

void draw(){
  background(0);
  
  // Get the next available client
  Client thisClient = myServer.available();
  // If the client is not null, and says something, display what it said
  if (thisClient !=null) {
    String clientMsg = thisClient.readString();
    if (clientMsg != null) {
      int p1 = clientMsg.indexOf(",");
      int p2 = clientMsg.indexOf(",", p1 + 1);
      println(clientMsg);
      println(p1 + ":" + p2); 
      
      if (p1 != -1 && p2 != -1) {
        roll = int(clientMsg.substring(0, p1));   
        pitch = int(clientMsg.substring(p1 + 1, p2));    
        yaw = int(clientMsg.substring(p2 + 1)); 
        println(roll + ":" + pitch + ":" + yaw); 
      }
    } 
  }
  
  lights();
  noStroke();
  pushMatrix();
  translate(100, height/2, 0);
  //radians
  rotateY(radians(roll));
  rotateX(radians(pitch));
  stroke(0,0,255);
  line(0,0,40,40);
  box(50);
  popMatrix();
}