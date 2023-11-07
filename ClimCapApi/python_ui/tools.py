#Fonctions de traitement
#_______________________________________________________________________

    def onGetFrequency(self):
        liste = self.fyv
        n = len(liste) # length of the signal
        k = np.arange(n)
        T = n/self.Fs
        frq = k/T # two sides frequency range
        frq = frq[:len(frq)//2] # one side frequency range

        Y = np.fft.fft(liste)/n # dft and normalization
        Y = Y[:n//2]

        pg.plot(frq,abs(Y)) # plotting the spectrum
        self.plot(self.fxv,self.fyv,self.fzv)

    def tr5 (self,Liste):
        minf,maxf=min(Liste),max(Liste)
        ind=min([Liste.index(minf),Liste.index(maxf)])
        for i in range(len(Liste)-1,0,-1):

            if Liste[i]>=0.05*maxf or Liste[i]<=0.05*minf :
                return (i/self.Fs-ind/self.Fs)

    def freq (self,Liste):
        maxl=np.max(Liste)
        indm=Liste.index(maxl)

        no=0 #nombre oscillation
        for i in range(indm+1,len(Liste)-1):
            p=(Liste[i]-Liste[i-1])/self.Fs
            p1=(Liste[i+1]-Liste[i])/self.Fs
            if p>0 and p1<0 :
                no+=1
                if Liste[i]<0.05*maxl and Liste[i]>0 :
                    f=no/((i-indm)/self.Fs) # retourne frequence moy sur la periode d'oscillation
                    return f
    
    def plot(self,Fx,Fy,Fz):
        T = self.xtime[1:]
        M=3.8 #masse du capteur+prise ouplaque
        start=0.5 #nombre de seconde avant la perturbation pour faire le 0
        fs=self.Fs #Hz
        Ft=[]

        Fxm=np.mean(Fx[0:int(fs*start)])   #faire le 0
        Fym=np.mean(Fy[0:int(fs*start)])   
        Fzm=np.mean(Fz[0:int(fs*start)])   
        for i in range(len(Fx)):
            Fx[i]-=Fxm
            Fy[i]-=Fym
            Fz[i]-=Fzm

        Ax,Ay,Az=[],[],[]
        for i in range(len(Fx)):
            
            Ax+=[Fx[i]/M]
            Ay+=[Fy[i]/M]
            Az+=[Fz[i]/M]
        #enleve la gravité
    
        Axm=np.mean(Ax[0:int(fs*start)])   #faire le 0
        Aym=np.mean(Ay[0:int(fs*start)])   
        Azm=np.mean(Az[0:int(fs*start)])   
        for i in range(len(Ax)):
            Ax[i]-=Axm
            Ay[i]-=Aym
            Az[i]-=Azm
        
        #♦vitesse a partir de l accel
        Vx,Vy,Vz=[0],[0],[0]
        vx,vy,vz=0,0,0
        for i in range(len(Ax)-1):
            vx+=(Ax[i]+Ax[i+1])/2/fs
            Vx.append(vx)
            vy+=(Ay[i]+Ay[i+1])/2/fs
            Vy.append(vy)
            vz+=(Az[i]+Az[i+1])/2/fs
            Vz.append(vz)

        #vitesse filtré
        fc=5
        w=fc/(fs/2)
        b, a = signal.butter(6, w, 'high')
        VXf = signal.filtfilt(b, a, Vx)
        VYf = signal.filtfilt(b, a, Vy)
        VZf = signal.filtfilt(b, a, Vz)
        
        # Position a partir de V et A non filtré
        PXf,PYf,PZf=[0],[0],[0]
        px,py,pz=0,0,0
        for i in range(len(Vx)-1):
            px+=(VXf[i]+VXf[i+1])/2/fs
            PXf.append(px*10**3)
            py+=(VYf[i]+VYf[i+1])/2/fs
            PYf.append(py*10**3)
            pz+=(VZf[i]+VZf[i+1])/2/fs
            PZf.append(pz*10**3)

    
        sc = MplCanvas(self, width=5, height=4, dpi=100)

        (ax1,ax3) = sc.figure.subplots(1,2)
        ax1.set_title(' Force & Accélération ',fontsize=16)

        ax3.set_title('Vitesse & Position ',fontsize=16)
        ax2 = ax1.twinx()
        ax4 = ax3.twinx()
        
        lines1,=ax1.plot(T,Fx,'c',label='Force X')
        lines2,=ax1.plot(T,Fy,'r',label='Force Y')
        lines3,=ax1.plot(T,Fz,'y',label='Force Z')
        ax1.grid(True)
        ax1.set_xlabel('Temps (s)', fontsize=12) 
        ax1.set_ylabel('Force (N)', fontsize=12) 
        
        lines4,=ax2.plot(T,Ax,label='Acc X')
        lines5,=ax2.plot(T,Ay,label='Acc Y')
        lines6,=ax2.plot(T,Az,label='Acc Z')
        ax2.grid(True)
        ax2.set_xlabel('Temps (s)', fontsize=12) 
        ax2.set_ylabel('Acc (m/s)', fontsize=12) 
        
        line1,=ax3.plot(T,VXf,'c',label='Vitesse X')
        line2,=ax3.plot(T,VYf,'r',label='Vitesse Y')
        line3,=ax3.plot(T,VZf,'y',label='Vitesse Z')
        ax3.grid(True)
        ax3.set_xlabel('Temps (s)', fontsize=12) 
        ax3.set_ylabel('Vitesse (m/s)', fontsize=12) 
        
        line4,=ax4.plot(T,PXf,label='Position X')
        line5,=ax4.plot(T,PYf,label='Position Y')
        line6,=ax4.plot(T,PZf,label='Position Z')
        ax4.grid(True)
        ax4.set_xlabel('Temps (s)', fontsize=12) 
        ax4.set_ylabel('Position (mm)', fontsize=12) 
        
        line7,=ax3.plot([], [], ' ', label='Tr 5 % =  '+str(self.tr5(Ay)))
        line8,=ax3.plot([], [], ' ', label='Fréquence =  '+str(self.freq(Az)))
        ax1.legend(handles=[lines1,lines2,lines3,lines4,lines5,lines6])
        ax3.legend(handles=[line1,line2,line3,line4,line5,line6,line7,line8])
        sc.show()
