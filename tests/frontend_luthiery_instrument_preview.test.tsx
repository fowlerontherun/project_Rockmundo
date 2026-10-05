import React from 'react';
import {render,screen} from '@testing-library/react';
import InstrumentPreview from '../frontend/src/crafting/InstrumentPreview';

describe('InstrumentPreview',()=>{
 it('renders named shape preview accessibly',()=>{render(<InstrumentPreview appearance={{instrument_type:'guitar',shape_key:'luthier.shape.guitar.coffin',primary_colour:'#111111',accent_colour:'#eeeeee',hardware_colour:'#cccccc',surface_sheen:'matte'}} label="Coffin guitar"/>);expect(screen.getByRole('img',{name:'Coffin guitar'})).toBeTruthy()});
 it('supports a headless shape without losing the instrument image',()=>{render(<InstrumentPreview appearance={{instrument_type:'guitar',shape_key:'luthier.shape.guitar.headless',primary_colour:'#111111'}} label="Headless guitar"/>);expect(screen.getByRole('img',{name:'Headless guitar'})).toBeTruthy()});
});
