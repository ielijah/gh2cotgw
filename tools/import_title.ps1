# Convert the generated source artwork to the existing Genesis title palette.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
public class TitleImport {
  public static void Run(string source, string destination, string preview) {
    int[,] palette={{0,0,0},{0,0,172},{205,68,32},{65,0,98},{98,0,139},{139,68,172},{172,68,205},{205,101,238},{32,0,65},{139,0,0},{172,0,0},{205,68,65},{238,68,98},{98,0,0},{205,137,238}};
    using(var input=new Bitmap(source)) using(var output=new Bitmap(192,88)) {
      byte[] indices=new byte[192*88];
      for(int y=0;y<88;y++) for(int x=0;x<192;x++) {
        double left=x*input.Width/192.0, right=(x+1)*input.Width/192.0;
        double top=y*input.Height/88.0, bottom=(y+1)*input.Height/88.0;
        double r=0,g=0,b=0,total=0;
        for(int sy=(int)top;sy<Math.Ceiling(bottom);sy++) for(int sx=(int)left;sx<Math.Ceiling(right);sx++) {
          double weight=(Math.Min(sx+1,right)-Math.Max(sx,left))*(Math.Min(sy+1,bottom)-Math.Max(sy,top));
          var c=input.GetPixel(sx,sy);r+=c.R*weight;g+=c.G*weight;b+=c.B*weight;total+=weight;
        }
        r/=total;g/=total;b/=total;
        int best=0;double distance=double.MaxValue;
        for(int i=0;i<15;i++) {
          double d=Math.Pow(r-palette[i,0],2)+Math.Pow(g-palette[i,1],2)+Math.Pow(b-palette[i,2],2);
          if(d<distance){distance=d;best=i;}
        }
        indices[y*192+x]=(byte)best;
        output.SetPixel(x,y,Color.FromArgb(palette[best,0],palette[best,1],palette[best,2]));
      }
      File.WriteAllBytes(destination,indices);
      output.Save(preview,ImageFormat.Png);
    }
  }
}
'@
$projectRoot = Split-Path $PSScriptRoot -Parent
[TitleImport]::Run((Join-Path $projectRoot 'assets/title-logo-source.png'),(Join-Path $projectRoot 'assets/title-logo-indexed.bin'),(Join-Path $projectRoot 'analysis/title-import-preview.png'))
