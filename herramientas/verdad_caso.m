function verdad_caso(entrada, salida)
% Simula en MATLAB (Antenna Toolbox, método de momentos) la placa que genera el proyecto y guarda S11, Z y directividad.
% Lo lanza herramientas/verdad_matlab.py: matlab -batch "verdad_caso('entrada.json','salida.json')".
% La entrada trae el cobre de F.Cu y B.Cu como anillos (x, y en mm), el contorno, el sustrato y el punto de alimentación.
d = jsondecode(fileread(entrada));
mm = 1e-3;

top = capa(d.cobre_superior, mm);
bot = capa(d.cobre_inferior, mm);
sus = dielectric('FR4');
sus.EpsilonR = d.er;
sus.LossTangent = d.tand;
sus.Thickness = d.h_mm*mm;

p = pcbStack;
p.BoardShape = antenna.Polygon('Vertices', [d.contorno.x(:)*mm, d.contorno.y(:)*mm, zeros(numel(d.contorno.x),1)]);
p.BoardThickness = d.h_mm*mm;
p.Layers = {top, sus, bot};
p.FeedLocations = [d.alimentacion_mm(1)*mm, d.alimentacion_mm(2)*mm, 1, 3];
p.FeedDiameter = 0.5*mm;
p.Conductor = metal('PEC');
mesh(p, 'MaxEdgeLength', d.malla_mm*mm);

fr = linspace(d.f_ini_MHz, d.f_fin_MHz, d.puntos)*1e6;
S = sparameters(p, fr, 50);
s11 = squeeze(S.Parameters);
z = 50*(1+s11)./(1-s11);
[~, i] = min(abs(s11));

% cruce de reactancia por cero, el más cercano al mínimo de S11 (como hace fase0.comun en openEMS)
x = imag(z); f_x = NaN;
cruces = find(sign(x(1:end-1)).*sign(x(2:end)) < 0);
if ~isempty(cruces)
    [~, j] = min(abs(cruces - i));
    k = cruces(j);
    f_x = fr(k) + (0 - x(k))*(fr(k+1)-fr(k))/(x(k+1)-x(k));
end

Dmax = NaN; Dgrid = [];
try
    if isfield(d, 'theta_deg')
        % rejilla de la interfaz: θ desde +z, φ desde +x; MATLAB usa elevación = 90 − θ
        fd = d.f_diagrama_MHz*1e6;
        Dgrid = pattern(p, fd, d.phi_deg(:)', 90 - d.theta_deg(:)');
        Dmax = max(Dgrid(:));
    else
        D = pattern(p, fr(i), 0:10:350, -90:10:90);
        Dmax = max(D(:));
    end
catch err
    warning('No se pudo calcular el diagrama: %s', err.message);
end

r = struct('f_min_S11_MHz', fr(i)/1e6, 'S11_min_dB', 20*log10(abs(s11(i))), ...
           'f_cruce_X_MHz', f_x/1e6, 'Z_en_minimo', [real(z(i)) imag(z(i))], ...
           'directividad_max_dBi', Dmax, 'f_MHz', fr/1e6, 'S11_dB', 20*log10(abs(s11(:))'), ...
           's11_re', real(s11(:))', 's11_im', imag(s11(:))', 'D_grid', Dgrid);
fid = fopen(salida, 'w'); fwrite(fid, jsonencode(r), 'char'); fclose(fid);
end

function forma = capa(anillos, mm)
% Une los polígonos de una capa. Cada anillo: poli (índice), hueco (0 exterior, 1 hueco), x, y.
forma = [];
if isempty(anillos), return; end
if ~isstruct(anillos), anillos = [anillos{:}]; end
for k = unique([anillos.poli])
    sel = anillos([anillos.poli] == k);
    ext = sel([sel.hueco] == 0);
    f = poligono(ext(1), mm);
    for h = sel([sel.hueco] == 1)
        f = f - poligono(h, mm);
    end
    if isempty(forma), forma = f; else, forma = forma + f; end
end
end

function q = poligono(a, mm)
q = antenna.Polygon('Vertices', [a.x(:)*mm, a.y(:)*mm, zeros(numel(a.x),1)]);
end
