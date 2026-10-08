"""BatteryEMS web application: REST + Socket.IO around the shared controller."""
from __future__ import annotations
import threading,time,os
from flask import Flask,render_template,jsonify,Response,request
from flask_socketio import SocketIO,emit
import config,db
from backend.controller import BatteryController
from services.historical_service import HistoricalDataService
from services.alarm_service import AlarmService

app=Flask(__name__); app.config["SECRET_KEY"]="batteryems"
socketio=SocketIO(app,cors_allowed_origins="*",async_mode="threading")
db.init_database(); controller=BatteryController()
controller.bms.seed_cycles(controller.repository.get_last_equivalent_full_cycles())
history_service=HistoricalDataService(); alarm_service=AlarmService()
_loop_started=False; _loop_lock=threading.Lock()

def history_payload(limit=None, downsample=None): return history_service.get_history(limit or config.MAX_HISTORY_POINTS, downsample=downsample)
def build_payload():
    live=controller.get_live_data()
    return {"schema_version":"1.0","timestamp":live["timestamp"],"bms":live["bms"],"ems":live["ems"],
            "hardware":live["hardware"],"simulation_running":live["simulation_running"],
            "alarms":alarm_service.evaluate(live["bms"]),"history":history_payload(),
            "cycle":controller.get_current_cycle_status()}

def emit_update(): socketio.emit("update",build_payload())
def background_loop():
    while True:
        if not controller.paused: emit_update()
        time.sleep(config.TICK_INTERVAL_SECONDS)
def start_loop():
    global _loop_started
    with _loop_lock:
        if not _loop_started: socketio.start_background_task(background_loop); _loop_started=True

@app.route("/")
def index(): return render_template("index.html")
@app.route("/health")
def health(): return jsonify({"status":"ok","service":"BatteryEMS","schema_version":"1.0"})
@app.route("/api/live")
@app.route("/api/v1/live")
def api_live(): return jsonify(build_payload())
@app.route("/api/history")
@app.route("/api/v1/history")
def api_history():
    requested_limit = request.args.get("limit", type=int)
    limit = requested_limit if requested_limit else config.HISTORY_TAB_MAX_POINTS
    downsample = request.args.get("downsample", type=int)
    return jsonify({"schema_version":"1.0","history":history_payload(limit, downsample)})
@app.route("/api/statistics")
@app.route("/api/v1/statistics")
def api_statistics(): return jsonify({"schema_version":"1.0","statistics":history_service.statistics()})
@app.route("/api/faults")
@app.route("/api/v1/faults")
def api_faults(): return jsonify({"schema_version":"1.0","faults":history_service.faults()})
@app.route("/robots.txt")
def robots(): return Response("User-agent: *\nAllow: /\nSitemap: /sitemap.xml\n",mimetype="text/plain")
@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    key = request.headers.get("X-API-Key") or request.args.get("key")
    if key != config.INGEST_API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    payload = request.get_json(force=True, silent=True) or {}
    required = {"cell_voltages", "current_a", "temperature_c"}
    if not required.issubset(payload.keys()):
        return jsonify({"error": "missing required fields"}), 400
    from hardware.ingest_store import store_reading
    try:
        store_reading(payload["cell_voltages"], payload["current_a"], payload["temperature_c"])
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True})

# --------------------------------------------------------------------
# CYCLE TESTING (additive). Pure logging/labeling -- no charger, load
# or relay is ever controlled by these endpoints.
# --------------------------------------------------------------------
@app.route("/api/cycles/start", methods=["POST"])
@app.route("/api/v1/cycles/start", methods=["POST"])
def api_cycle_start():
    payload = request.get_json(silent=True) or {}
    test_state = payload.get("test_state", "CHARGE")
    cycle = controller.start_cycle(test_state)
    emit_update()
    return jsonify({"schema_version": "1.0", "cycle": cycle})

@app.route("/api/cycles/stop", methods=["POST"])
@app.route("/api/v1/cycles/stop", methods=["POST"])
def api_cycle_stop():
    stopped_id = controller.stop_cycle()
    emit_update()
    return jsonify({"schema_version": "1.0", "stopped_cycle_id": stopped_id})

@app.route("/api/cycles")
@app.route("/api/v1/cycles")
def api_cycles_list():
    return jsonify({"schema_version": "1.0", "cycles": controller.get_cycles()})

@app.route("/api/cycles/<int:cycle_id>")
@app.route("/api/v1/cycles/<int:cycle_id>")
def api_cycle_detail(cycle_id):
    cycles = controller.get_cycles()
    cycle = next((c for c in cycles if c["id"] == cycle_id), None)
    readings = controller.get_cycle_readings(cycle_id)
    return jsonify({
        "schema_version": "1.0",
        "cycle": cycle,
        "readings": {
            "timestamps": [r["timestamp"] for r in readings],
            "voltage": [float(r["pack_voltage"]) for r in readings],
            "current": [float(r["pack_current"]) for r in readings],
            "temperature": [float(r["temperature"]) for r in readings],
            "soc": [float(r["soc_percent"]) for r in readings],
        }
    })

@app.route("/sitemap.xml")
def sitemap():
    host=request.host_url.rstrip("/")
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+host+'/</loc></url></urlset>'
    return Response(xml,mimetype="application/xml")
@socketio.on("connect")
def on_connect(): emit("update",build_payload())
@socketio.on("command")
def handle_command(message):
    message=message or {}; command=message.get("type")
    actions={"grid_up":controller.grid_up,"grid_down":controller.grid_down,"clear":controller.clear_faults,
             "pause":controller.pause,"resume":controller.resume,"reset":controller.reset}
    if command=="fault": controller.inject_fault(message.get("fault","overvoltage"))
    elif command=="set_device": controller.set_active_device(message.get("device","simulator")); controller.connect_device()
    elif command in actions: actions[command]()
    emit_update()
@socketio.on("request_update")
def request_update(): emit_update()
if __name__=="__main__":
    start_loop(); socketio.run(app,host=os.getenv("HOST","0.0.0.0"),port=int(os.getenv("PORT") or "5000"),debug=False,allow_unsafe_werkzeug=True)
