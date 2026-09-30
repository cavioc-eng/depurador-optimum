import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Depurador ViciDial - Optimum Home",
    page_icon="📞",
    layout="wide"
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "password" not in st.session_state:
    st.session_state.password = "optimum2026*"
if "must_change_password" not in st.session_state:
    st.session_state.must_change_password = True
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #b89742;'>Optimum Home - Sistema de Depuración</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: gray;'>Módulo de Gestión de Leads ViciDial</h4>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Correo electrónico", value="juan.lopez@optimumhome.org")
            pwd = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Iniciar Sesión")
            
            if submit:
                if email.strip().lower() == "juan.lopez@optimumhome.org" and pwd == st.session_state.password:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique su correo y contraseña.")

def change_password_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("Por seguridad, debe cambiar su contraseña temporal en su primer acceso.")
        with st.form("pwd_form"):
            new_pwd = st.text_input("Nueva contraseña", type="password")
            confirm_pwd = st.text_input("Confirme la nueva contraseña", type="password")
            submit_pwd = st.form_submit_button("Actualizar Contraseña")
            
            if submit_pwd:
                if new_pwd and new_pwd == confirm_pwd:
                    st.session_state.password = new_pwd
                    st.session_state.must_change_password = False
                    st.success("¡Contraseña actualizada con éxito!")
                    st.rerun()
                else:
                    st.error("Las contraseñas no coinciden o están vacías.")

def main_app():
    with st.sidebar:
        try:
            st.image("logo_optimum.png", width=200)
        except:
            st.warning("No se encontró el logo_optimum.png en el escritorio.")
        
        st.markdown(f"**Usuario:** {st.session_state.user_email}")
        st.markdown("---")
        if st.button("Cerrar Sesión"):
            st.session_state.authenticated = False
            st.session_state.must_change_password = True
            st.rerun()
            
        st.markdown("### Historial de Bitácora")
        if st.session_state.audit_log:
            for log in reversed(st.session_state.audit_log[-5:]):
                st.caption(f"[{log['fecha']}] {log['archivo']} ({log['limpios']} limpios)")
        else:
            st.caption("Sin registros aún en la sesión.")

    st.title("Panel de Control - Depuración de Listas ViciDial")
    st.markdown("Suba el archivo exportado desde ViciDial para procesar automáticamente el filtrado de estados no deseados.")

    uploaded_file = st.file_uploader("Seleccione el archivo de leads (CSV o TXT/Excel)", type=["csv", "txt", "xlsx", "xls"])

    if uploaded_file is not None:
        try:
            filename = uploaded_file.name
            if filename.endswith('.csv') or filename.endswith('.txt'):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8', on_bad_lines='skip', sep=None, engine='python')
                except:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin1', on_bad_lines='skip', sep=None, engine='python')
            else:
                df = pd.read_excel(uploaded_file)
            
            df.columns = df.columns.astype(str).str.strip()

            st.success(f"Archivo cargado correctamente: **{filename}**")
            st.metric("Total de registros cargados", len(df))

            if 'status' not in df.columns:
                st.error("El archivo no contiene la columna 'status'. Verifique que sea un formato válido de ViciDial.")
            else:
                with st.expander("Ver distribución de estatus originales"):
                    st.write(df['status'].value_counts())

                unwanted_statuses = ['AB', 'ADC', 'DAIR', 'D-Air', 'DNC', 'DNCL', 'DNC L', 'Do Not', 'NI', 'Wrong']
                
                df_clean = df[~df['status'].isin(unwanted_statuses)]
                df_excluded = df[df['status'].isin(unwanted_statuses)]

                col1, col2 = st.columns(2)
                col1.metric("Registros Limpios (Para ViciDial)", len(df_clean))
                col2.metric("Registros Excluidos (Para Auditoría)", len(df_excluded))

                st.markdown("---")
                st.subheader("Archivos Generados listos para descarga")

                clean_csv = df_clean.to_csv(index=False).encode('utf-8')
                excluded_csv = df_excluded.to_csv(index=False).encode('utf-8')

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                d_col1, d_col2 = st.columns(2)
                
                with d_col1:
                    st.download_button(
                        label="📥 Descargar CSV Depurado (Para ViciDial)",
                        data=clean_csv,
                        file_name=f"Depurado_{filename.split('.')[0]}_{timestamp}.csv",
                        mime="text/csv",
                    )
                
                with d_col2:
                    st.download_button(
                        label="📥 Descargar Lista de Excluidos (Para Base Maestra)",
                        data=excluded_csv,
                        file_name=f"Excluidos_{filename.split('.')[0]}_{timestamp}.csv",
                        mime="text/csv",
                    )

                log_entry = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "archivo": filename,
                    "originales": len(df),
                    "limpios": len(df_clean),
                    "excluidos": len(df_excluded)
                }
                if not st.session_state.audit_log or st.session_state.audit_log[-1]["archivo"] != filename:
                    st.session_state.audit_log.append(log_entry)

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {e}")

if not st.session_state.authenticated:
    login_screen()
elif st.session_state.must_change_password:
    change_password_screen()
else:
    main_app()
