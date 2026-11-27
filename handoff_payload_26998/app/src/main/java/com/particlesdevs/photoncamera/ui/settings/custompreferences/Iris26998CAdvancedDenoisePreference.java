package com.particlesdevs.photoncamera.ui.settings.custompreferences;

import android.app.AlertDialog;
import android.content.Context;
import android.text.InputType;
import android.util.AttributeSet;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.TextView;
import com.particlesdevs.photoncamera.R;
import com.particlesdevs.photoncamera.settings.Iris26998CDenoiseSettings;
import java.util.Locale;

/** Iris switch + existing seekbar layout, transactional advanced popup. */
public final class Iris26998CAdvancedDenoisePreference extends ManagedSwitchPreference {
    private boolean rebinding;
    private String lens;
    public Iris26998CAdvancedDenoisePreference(Context c, AttributeSet a){super(c,a);}
    private boolean chroma(){return getKey()!=null && getKey().endsWith("chroma");}
    @Override public boolean getPersistedBoolean(boolean fallback){return Iris26998CDenoiseSettings.enabled(getContext(),lens,chroma());}
    @Override public boolean persistBoolean(boolean value){return rebinding;}
    public void bindLens(String id,boolean visible){lens=id;setVisible(visible);setEnabled(visible);refresh();}
    private void refresh(){rebinding=true;try{setChecked(getPersistedBoolean(false));}finally{rebinding=false;}}
    @Override protected void onClick(){
        if(lens==null || lens.trim().isEmpty())return;
        if(isChecked()){Iris26998CDenoiseSettings.setEnabled(getContext(),lens,chroma(),false);refresh();}
        else showBands();
    }
    @Override public void onBindViewHolder(androidx.preference.PreferenceViewHolder holder){
        super.onBindViewHolder(holder);
        // Clicking the label while already ON reopens the dialog; switch remains a direct OFF action.
        View title=holder.findViewById(android.R.id.title);
        View summary=holder.findViewById(android.R.id.summary);
        View widget=holder.findViewById(androidx.preference.R.id.switchWidget);
        if(widget instanceof androidx.appcompat.widget.SwitchCompat){
            androidx.appcompat.widget.SwitchCompat toggle=(androidx.appcompat.widget.SwitchCompat)widget;
            toggle.setOnCheckedChangeListener(null);
            toggle.setChecked(isChecked());
            toggle.setOnClickListener(v->{onClick();toggle.setChecked(isChecked());});
        }
        if(title!=null)title.setOnClickListener(v->{if(isEnabled()&&lens!=null)showBands();});
        if(summary!=null)summary.setOnClickListener(v->{if(isEnabled()&&lens!=null)showBands();});
    }
    private void showBands(){
        final Context c=getContext();final String selected=lens;final boolean isChroma=chroma();
        final float[] draft=Iris26998CDenoiseSettings.bands(c,selected,isChroma);
        final SeekBar[] sliders=new SeekBar[5];final TextView[] values=new TextView[5];
        LinearLayout rows=new LinearLayout(c);rows.setOrientation(LinearLayout.VERTICAL);
        for(int i=0;i<5;i++){
            final int band=i;
            View row=LayoutInflater.from(c).inflate(R.layout.preference_seekbar,rows,false);
            TextView title=row.findViewById(android.R.id.title);title.setText("Band "+(i+1));title.setGravity(android.view.Gravity.START);
            TextView summary=row.findViewById(android.R.id.summary);summary.setText("SNR-adaptive multiplier");
            View icon=row.findViewById(android.R.id.icon);icon.setVisibility(View.INVISIBLE);
            SeekBar slider=row.findViewById(R.id.seekbar);TextView value=row.findViewById(R.id.seekbar_value);
            sliders[i]=slider;values[i]=value;slider.setMax(1600);slider.setProgress(Math.round(draft[i]*100f));value.setText(format(draft[i]));
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
                public void onProgressChanged(SeekBar s,int progress,boolean fromUser){if(fromUser){draft[band]=progress/100f;value.setText(format(draft[band]));}}
                public void onStartTrackingTouch(SeekBar s){} public void onStopTrackingTouch(SeekBar s){}
            });
            value.setOnClickListener(v->{
                EditText input=new EditText(c);input.setInputType(InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL);input.setText(Float.toString(draft[band]));input.setSelectAllOnFocus(true);
                AlertDialog precise=new AlertDialog.Builder(c).setTitle("Band "+(band+1)).setMessage("Enter precise value (0–16)\nDefault: 1.00").setView(input).setPositiveButton("SET",null).setNegativeButton("CANCEL",null).setNeutralButton("RESET",null).create();
                precise.setOnShowListener(d->{precise.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w->{try{float f=Float.parseFloat(input.getText().toString());if(!Iris26998CDenoiseSettings.valid(f))throw new NumberFormatException();draft[band]=f;slider.setProgress(Math.round(f*100f));value.setText(format(f));precise.dismiss();}catch(NumberFormatException e){input.setError("Enter a finite number from 0 to 16");}});precise.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(w->input.setText("1.00"));});precise.show();
            });rows.addView(row);
        }
        ScrollView scroll=new ScrollView(c);scroll.addView(rows);
        AlertDialog dialog=new AlertDialog.Builder(c).setTitle(getTitle()).setView(scroll).setPositiveButton("SET",(d,w)->{if(selected.equals(lens)){Iris26998CDenoiseSettings.saveEnabledBands(c,selected,isChroma,draft);refresh();}}).setNegativeButton("CANCEL",(d,w)->refresh()).setNeutralButton("RESET",null).create();
        dialog.setOnShowListener(d->dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->{for(int i=0;i<5;i++){draft[i]=1f;sliders[i].setProgress(100);values[i].setText("1.00");}}));dialog.show();
    }
    private static String format(float v){String exact=Float.toString(v);
        return exact.indexOf('E')>=0 || exact.indexOf('.')<exact.length()-2 ? exact : String.format(Locale.ROOT,"%.2f",v);}
}
