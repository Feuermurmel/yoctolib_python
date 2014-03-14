#*********************************************************************
#*
#* $Id: yocto_refframe.py 15376 2014-03-10 16:22:13Z seb $
#*
#* Implements yFindRefFrame(), the high-level API for RefFrame functions
#*
#* - - - - - - - - - License information: - - - - - - - - - 
#*
#*  Copyright (C) 2011 and beyond by Yoctopuce Sarl, Switzerland.
#*
#*  Yoctopuce Sarl (hereafter Licensor) grants to you a perpetual
#*  non-exclusive license to use, modify, copy and integrate this
#*  file into your software for the sole purpose of interfacing
#*  with Yoctopuce products.
#*
#*  You may reproduce and distribute copies of this file in
#*  source or object form, as long as the sole purpose of this
#*  code is to interface with Yoctopuce products. You must retain
#*  this notice in the distributed source file.
#*
#*  You should refer to Yoctopuce General Terms and Conditions
#*  for additional information regarding your rights and
#*  obligations.
#*
#*  THE SOFTWARE AND DOCUMENTATION ARE PROVIDED 'AS IS' WITHOUT
#*  WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING 
#*  WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, FITNESS
#*  FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO
#*  EVENT SHALL LICENSOR BE LIABLE FOR ANY INCIDENTAL, SPECIAL,
#*  INDIRECT OR CONSEQUENTIAL DAMAGES, LOST PROFITS OR LOST DATA,
#*  COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY OR 
#*  SERVICES, ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT 
#*  LIMITED TO ANY DEFENSE THEREOF), ANY CLAIMS FOR INDEMNITY OR
#*  CONTRIBUTION, OR OTHER SIMILAR COSTS, WHETHER ASSERTED ON THE
#*  BASIS OF CONTRACT, TORT (INCLUDING NEGLIGENCE), BREACH OF
#*  WARRANTY, OR OTHERWISE.
#*
#*********************************************************************/


__docformat__ = 'restructuredtext en'
from yocto_api import *


#--- (YRefFrame class start)
#noinspection PyProtectedMember
class YRefFrame(YFunction):
    """
    This class is used to setup the base orientation of the Yocto-3D, so that
    the orientation functions, relative to the earth surface plane, use
    the proper reference frame. The class also implements a tridimensional
    sensor calibration process, which can compensate for local variations
    of standard gravity and improve the precision of the tilt sensors.
    
    """
#--- (end of YRefFrame class start)
    #--- (YRefFrame return codes)
    #--- (end of YRefFrame return codes)
    #--- (YRefFrame definitions)
    class MOUNTPOSITION:
        def __init__(self):
            pass
        BOTTOM, TOP, FRONT, RIGHT, REAR, LEFT = range(6)
    class MOUNTORIENTATION:
        def __init__(self):
            pass
        TWELVE, THREE, SIX, NINE = range(4)
    MOUNTPOS_INVALID = YAPI.INVALID_UINT
    BEARING_INVALID = YAPI.INVALID_DOUBLE
    CALIBRATIONPARAM_INVALID = YAPI.INVALID_STRING
    #--- (end of YRefFrame definitions)

    def __init__(self, func):
        super(YRefFrame, self).__init__(func)
        self._className = 'RefFrame'
        #--- (YRefFrame attributes)
        self._callback = None
        self._mountPos = YRefFrame.MOUNTPOS_INVALID
        self._bearing = YRefFrame.BEARING_INVALID
        self._calibrationParam = YRefFrame.CALIBRATIONPARAM_INVALID
        self._calibStage = 0
        self._calibStageHint = ''
        self._calibStageProgress = 0
        self._calibProgress = 0
        self._calibLogMsg = ''
        self._calibSavedParams = ''
        self._calibCount = 0
        self._calibInternalPos = 0
        self._calibPrevTick = 0
        self._calibOrient = []
        self._calibDataAccX = []
        self._calibDataAccY = []
        self._calibDataAccZ = []
        self._calibDataAcc = []
        self._calibAccXOfs = 0
        self._calibAccYOfs = 0
        self._calibAccZOfs = 0
        self._calibAccXScale = 0
        self._calibAccYScale = 0
        self._calibAccZScale = 0
        #--- (end of YRefFrame attributes)

    #--- (YRefFrame implementation)
    def _parseAttr(self, member):
        if member.name == "mountPos":
            self._mountPos = member.ivalue
            return 1
        if member.name == "bearing":
            self._bearing = member.ivalue / 65536.0
            return 1
        if member.name == "calibrationParam":
            self._calibrationParam = member.svalue
            return 1
        super(YRefFrame, self)._parseAttr(member)

    def get_mountPos(self):
        if self._cacheExpiration <= YAPI.GetTickCount():
            if self.load(YAPI.DefaultCacheValidity) != YAPI.SUCCESS:
                return YRefFrame.MOUNTPOS_INVALID
        return self._mountPos

    def set_mountPos(self, newval):
        rest_val = str(newval)
        return self._setAttr("mountPos", rest_val)

    def set_bearing(self, newval):
        """
        Changes the reference bearing used by the compass. The relative bearing
        indicated by the compass is the difference between the measured magnetic
        heading and the reference bearing indicated here.
        
        For instance, if you setup as reference bearing the value of the earth
        magnetic declination, the compass will provide the orientation relative
        to the geographic North.
        
        Similarly, when the sensor is not mounted along the standard directions
        because it has an additional yaw angle, you can set this angle in the reference
        bearing so that the compass provides the expected natural direction.
        
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.
        
        @param newval : a floating point number corresponding to the reference bearing used by the compass
        
        @return YAPI.SUCCESS if the call succeeds.
        
        On failure, throws an exception or returns a negative error code.
        """
        rest_val = str(round(newval * 65536.0, 1))
        return self._setAttr("bearing", rest_val)

    def get_bearing(self):
        """
        Returns the reference bearing used by the compass. The relative bearing
        indicated by the compass is the difference between the measured magnetic
        heading and the reference bearing indicated here.
        
        @return a floating point number corresponding to the reference bearing used by the compass
        
        On failure, throws an exception or returns YRefFrame.BEARING_INVALID.
        """
        if self._cacheExpiration <= YAPI.GetTickCount():
            if self.load(YAPI.DefaultCacheValidity) != YAPI.SUCCESS:
                return YRefFrame.BEARING_INVALID
        return self._bearing

    def get_calibrationParam(self):
        if self._cacheExpiration <= YAPI.GetTickCount():
            if self.load(YAPI.DefaultCacheValidity) != YAPI.SUCCESS:
                return YRefFrame.CALIBRATIONPARAM_INVALID
        return self._calibrationParam

    def set_calibrationParam(self, newval):
        rest_val = newval
        return self._setAttr("calibrationParam", rest_val)

    @staticmethod
    def FindRefFrame(func):
        """
        Retrieves a reference frame for a given identifier.
        The identifier can be specified using several formats:
        <ul>
        <li>FunctionLogicalName</li>
        <li>ModuleSerialNumber.FunctionIdentifier</li>
        <li>ModuleSerialNumber.FunctionLogicalName</li>
        <li>ModuleLogicalName.FunctionIdentifier</li>
        <li>ModuleLogicalName.FunctionLogicalName</li>
        </ul>
        
        This function does not require that the reference frame is online at the time
        it is invoked. The returned object is nevertheless valid.
        Use the method YRefFrame.isOnline() to test if the reference frame is
        indeed online at a given time. In case of ambiguity when looking for
        a reference frame by logical name, no error is notified: the first instance
        found is returned. The search is performed first by hardware name,
        then by logical name.
        
        @param func : a string that uniquely characterizes the reference frame
        
        @return a YRefFrame object allowing you to drive the reference frame.
        """
        # obj
        obj = YFunction._FindFromCache("RefFrame", func)
        if obj is None:
            obj = YRefFrame(func)
            YFunction._AddToCache("RefFrame", func, obj)
        return obj

    def get_mountPosition(self):
        """
        Returns the installation position of the device, as configured
        in order to define the reference frame for the compass and the
        pitch/roll tilt sensors.
        
        @return a value among the YRefFrame.MOUNTPOSITION enumeration
                (YRefFrame.MOUNTPOSITION_BOTTOM,   YRefFrame.MOUNTPOSITION_TOP,
                YRefFrame.MOUNTPOSITION_FRONT,    YRefFrame.MOUNTPOSITION_RIGHT,
                YRefFrame.MOUNTPOSITION_REAR,     YRefFrame.MOUNTPOSITION_LEFT),
                corresponding to the installation in a box, on one of the six faces.
        
        On failure, throws an exception or returns a negative error code.
        """
        # pos
        pos = self.get_mountPos()
        return ((pos) >> (2))

    def get_mountOrientation(self):
        """
        Returns the installation orientation of the device, as configured
        in order to define the reference frame for the compass and the
        pitch/roll tilt sensors.
        
        @return a value among the enumeration YRefFrame.MOUNTORIENTATION
                (YRefFrame.MOUNTORIENTATION_TWELVE, YRefFrame.MOUNTORIENTATION_THREE,
                YRefFrame.MOUNTORIENTATION_SIX,     YRefFrame.MOUNTORIENTATION_NINE)
                corresponding to the orientation of the "X" arrow on the device,
                as on a clock dial seen from an observer in the center of the box.
                On the bottom face, the 12H orientation points to the front, while
                on the top face, the 12H orientation points to the rear.
        
        On failure, throws an exception or returns a negative error code.
        """
        # pos
        pos = self.get_mountPos()
        return ((pos) & (3))

    def set_mountPosition(self, position, orientation):
        """
        Changes the compass and tilt sensor frame of reference. The magnetic compass
        and the tilt sensors (pitch and roll) naturally work in the plane
        parallel to the earth surface. In case the device is not installed upright
        and horizontally, you must select its reference orientation (parallel to
        the earth surface) so that the measures are made relative to this position.
        
        @param position: a value among the YRefFrame.MOUNTPOSITION enumeration
                (YRefFrame.MOUNTPOSITION_BOTTOM,   YRefFrame.MOUNTPOSITION_TOP,
                YRefFrame.MOUNTPOSITION_FRONT,    YRefFrame.MOUNTPOSITION_RIGHT,
                YRefFrame.MOUNTPOSITION_REAR,     YRefFrame.MOUNTPOSITION_LEFT),
                corresponding to the installation in a box, on one of the six faces.
        @param orientation: a value among the enumeration YRefFrame.MOUNTORIENTATION
                (YRefFrame.MOUNTORIENTATION_TWELVE, YRefFrame.MOUNTORIENTATION_THREE,
                YRefFrame.MOUNTORIENTATION_SIX,     YRefFrame.MOUNTORIENTATION_NINE)
                corresponding to the orientation of the "X" arrow on the device,
                as on a clock dial seen from an observer in the center of the box.
                On the bottom face, the 12H orientation points to the front, while
                on the top face, the 12H orientation points to the rear.
        
        Remember to call the saveToFlash()
        method of the module if the modification must be kept.
        
        On failure, throws an exception or returns a negative error code.
        """
        # pos
        pos = ((position) << (2)) + orientation
        return self.set_mountPos(pos)

    def _calibSort(self, start, stopidx):
        # idx
        # changed
        # a
        # b
        # xa
        # xb
        
        # // bubble sort is good since we will re-sort again after offset adjustment
        changed = 1
        while changed > 0:
            changed = 0
            a = self._calibDataAcc[start]
            idx = start + 1
            while idx < stopidx:
                b = self._calibDataAcc[idx]
                if a > b:
                    self._calibDataAcc[ idx-1] = b
                    self._calibDataAcc[ idx] = a
                    xa = self._calibDataAccX[idx-1]
                    xb = self._calibDataAccX[idx]
                    self._calibDataAccX[ idx-1] = xb
                    self._calibDataAccX[ idx] = xa
                    xa = self._calibDataAccY[idx-1]
                    xb = self._calibDataAccY[idx]
                    self._calibDataAccY[ idx-1] = xb
                    self._calibDataAccY[ idx] = xa
                    xa = self._calibDataAccZ[idx-1]
                    xb = self._calibDataAccZ[idx]
                    self._calibDataAccZ[ idx-1] = xb
                    self._calibDataAccZ[ idx] = xa
                    changed = changed + 1
                else:
                    a = b
                idx = idx + 1
        return 0

    def start3DCalibration(self):
        """
        Initiates the sensors tridimensional calibration process.
        This calibration is used at low level for inertial position estimation
        and to enhance the precision of the tilt sensors.
        
        After calling this method, the device should be moved according to the
        instructions provided by method get_3DCalibrationHint,
        and more3DCalibration should be invoked about 5 times per second.
        The calibration procedure is completed when the method
        get_3DCalibrationProgress returns 100. At this point,
        the computed calibration parameters can be applied using method
        save3DCalibration. The calibration process can be canceled
        at any time using method cancel3DCalibration.
        
        On failure, throws an exception or returns a negative error code.
        """
        # // may throw an exception
        if not (self.isOnline()):
            return YAPI.DEVICE_NOT_FOUND
        if self._calibStage != 0:
            self.cancel3DCalibration()
        self._calibSavedParams = self.get_calibrationParam()
        self.set_calibrationParam("0")
        self._calibCount = 50
        self._calibStage = 1
        self._calibStageHint = "Set down the device on a steady horizontal surface"
        self._calibStageProgress = 0
        self._calibProgress = 1
        self._calibInternalPos = 0
        self._calibPrevTick = ((YAPI.GetTickCount()) & (0x7FFFFFFF))
        del self._calibOrient[:]
        del self._calibDataAccX[:]
        del self._calibDataAccY[:]
        del self._calibDataAccZ[:]
        del self._calibDataAcc[:]
        return YAPI.SUCCESS

    def more3DCalibration(self):
        """
        Continues the sensors tridimensional calibration process previously
        initiated using method start3DCalibration.
        This method should be called approximately 5 times per second, while
        positioning the device according to the instructions provided by method
        get_3DCalibrationHint. Note that the instructions change during
        the calibration process.
        
        On failure, throws an exception or returns a negative error code.
        """
        # // may throw an exception
        # currTick
        # jsonData
        # xVal
        # yVal
        # zVal
        # xSq
        # ySq
        # zSq
        # norm
        # orient
        # idx
        # pos
        # err
        # // make sure calibration has been started
        if self._calibStage == 0:
            return YAPI.INVALID_ARGUMENT
        if self._calibProgress == 100:
            return YAPI.SUCCESS
        
        # // make sure we leave at least 160ms between samples
        currTick =  ((YAPI.GetTickCount()) & (0x7FFFFFFF))
        if ((currTick - self._calibPrevTick) & (0x7FFFFFFF)) < 160:
            return YAPI.SUCCESS
        # // load current accelerometer values, make sure we are on a straight angle
        # // (default timeout to 0,5 sec without reading measure when out of range)
        self._calibStageHint = "Set down the device on a steady horizontal surface"
        self._calibPrevTick = ((currTick + 500) & (0x7FFFFFFF))
        jsonData = self._download("api/accelerometer.json")
        xVal = int(self._json_get_key(jsonData, "xValue")) / 65536.0
        yVal = int(self._json_get_key(jsonData, "yValue")) / 65536.0
        zVal = int(self._json_get_key(jsonData, "zValue")) / 65536.0
        xSq = xVal * xVal
        if xSq >= 0.04 and xSq < 0.64:
            return YAPI.SUCCESS
        if xSq >= 1.44:
            return YAPI.SUCCESS
        ySq = yVal * yVal
        if ySq >= 0.04 and ySq < 0.64:
            return YAPI.SUCCESS
        if ySq >= 1.44:
            return YAPI.SUCCESS
        zSq = zVal * zVal
        if zSq >= 0.04 and zSq < 0.64:
            return YAPI.SUCCESS
        if zSq >= 1.44:
            return YAPI.SUCCESS
        norm = sqrt(xSq + ySq + zSq)
        if norm < 0.8 or norm > 1.2:
            return YAPI.SUCCESS
        self._calibPrevTick = currTick
        
        # // Determine the device orientation index
        if zSq > 0.5:
            if zVal > 0:
                orient = 0
            else:
                orient = 1
        if xSq > 0.5:
            if xVal > 0:
                orient = 2
            else:
                orient = 3
        if ySq > 0.5:
            if yVal > 0:
                orient = 4
            else:
                orient = 5
        
        # // Discard measures that are not in the proper orientation
        if self._calibStageProgress == 0:
            #
            idx = 0
            err = 0
            while idx + 1 < self._calibStage:
                if self._calibOrient[idx] == orient:
                    err = 1
                idx = idx + 1
            if err != 0:
                self._calibStageHint = "Turn the device on another face"
                return YAPI.SUCCESS
            self._calibOrient.append(orient)
        else:
            #
            if orient != self._calibOrient[self._calibStage-1]:
                self._calibStageHint = "Not yet done, please move back to the previous face"
                return YAPI.SUCCESS
        
        # // Save measure
        self._calibStageHint = "calibrating.."
        self._calibDataAccX.append(xVal)
        self._calibDataAccY.append(yVal)
        self._calibDataAccZ.append(zVal)
        self._calibDataAcc.append(norm)
        self._calibInternalPos = self._calibInternalPos + 1
        self._calibProgress = 1 + 16 * (self._calibStage - 1) + ((16 * self._calibInternalPos) / (self._calibCount))
        if self._calibInternalPos < self._calibCount:
            self._calibStageProgress = 1 + ((99 * self._calibInternalPos) / (self._calibCount))
            return YAPI.SUCCESS
        
        # // Stage done, compute preliminary result
        pos = (self._calibStage - 1) * self._calibCount
        self._calibSort(pos, pos + self._calibCount)
        pos = pos + ((self._calibCount) / (2))
        self._calibLogMsg = "Stage " + str(int(self._calibStage)) + ": median is " + str(int(round(1000*self._calibDataAccX[pos]))) + "," + str(int(round(1000*self._calibDataAccY[pos]))) + "," + str(int(round(1000*self._calibDataAccZ[pos])))
        
        # // move to next stage
        self._calibStage = self._calibStage + 1
        if self._calibStage < 7:
            self._calibStageHint = "Turn the device on another face"
            self._calibPrevTick = ((currTick + 500) & (0x7FFFFFFF))
            self._calibStageProgress = 0
            self._calibInternalPos = 0
            return YAPI.SUCCESS
        # // Data collection completed, compute accelerometer shift
        xVal = 0
        yVal = 0
        zVal = 0
        idx = 0
        while idx < 6:
            pos = idx * self._calibCount + ((self._calibCount) / (2))
            orient = self._calibOrient[idx]
            if orient == 0 or orient == 1:
                zVal = zVal + self._calibDataAccZ[pos]
            if orient == 2 or orient == 3:
                xVal = xVal + self._calibDataAccX[pos]
            if orient == 4 or orient == 5:
                yVal = yVal + self._calibDataAccY[pos]
            idx = idx + 1
        self._calibAccXOfs = xVal / 2.0
        self._calibAccYOfs = yVal / 2.0
        self._calibAccZOfs = zVal / 2.0
        
        # // Recompute all norms, taking into account the computed shift, and re-sort
        pos = 0
        while pos < len(self._calibDataAcc):
            xVal = self._calibDataAccX[pos] - self._calibAccXOfs
            yVal = self._calibDataAccY[pos] - self._calibAccYOfs
            zVal = self._calibDataAccZ[pos] - self._calibAccZOfs
            norm = sqrt(xVal * xVal + yVal * yVal + zVal * zVal)
            self._calibDataAcc[ pos] = norm
            pos = pos + 1
        idx = 0
        while idx < 6:
            pos = idx * self._calibCount
            self._calibSort(pos, pos + self._calibCount)
            idx = idx + 1
        
        # // Compute the scaling factor for each axis
        xVal = 0
        yVal = 0
        zVal = 0
        idx = 0
        while idx < 6:
            pos = idx * self._calibCount + ((self._calibCount) / (2))
            orient = self._calibOrient[idx]
            if orient == 0 or orient == 1:
                zVal = zVal + self._calibDataAcc[pos]
            if orient == 2 or orient == 3:
                xVal = xVal + self._calibDataAcc[pos]
            if orient == 4 or orient == 5:
                yVal = yVal + self._calibDataAcc[pos]
            idx = idx + 1
        self._calibAccXScale = xVal / 2.0
        self._calibAccYScale = yVal / 2.0
        self._calibAccZScale = zVal / 2.0
        
        # // Report completion
        self._calibProgress = 100
        self._calibStageHint = "Calibration data ready for saving"
        return YAPI.SUCCESS

    def get_3DCalibrationHint(self):
        """
        Returns instructions to proceed to the tridimensional calibration initiated with
        method start3DCalibration.
        
        @return a character string.
        """
        return self._calibStageHint

    def get_3DCalibrationProgress(self):
        """
        Returns the global process indicator for the tridimensional calibration
        initiated with method start3DCalibration.
        
        @return an integer between 0 (not started) and 100 (stage completed).
        """
        return self._calibProgress

    def get_3DCalibrationStage(self):
        """
        Returns index of the current stage of the calibration
        initiated with method start3DCalibration.
        
        @return an integer, growing each time a calibration stage is completed.
        """
        return self._calibStage

    def get_3DCalibrationStageProgress(self):
        """
        Returns the process indicator for the current stage of the calibration
        initiated with method start3DCalibration.
        
        @return an integer between 0 (not started) and 100 (stage completed).
        """
        return self._calibStageProgress

    def get_3DCalibrationLogMsg(self):
        """
        Returns the latest log message from the calibration process.
        When no new message is available, returns an empty string.
        
        @return a character string.
        """
        # msg
        msg = self._calibLogMsg
        self._calibLogMsg = ""
        return msg

    def save3DCalibration(self):
        """
        Applies the sensors tridimensional calibration parameters that have just been computed.
        Remember to call the saveToFlash()  method of the module if the changes
        must be kept when the device is restarted.
        
        On failure, throws an exception or returns a negative error code.
        """
        # // may throw an exception
        # shiftX
        # shiftY
        # shiftZ
        # scaleExp
        # scaleX
        # scaleY
        # scaleZ
        # scaleLo
        # scaleHi
        # newcalib
        if self._calibProgress != 100:
            return YAPI.INVALID_ARGUMENT
        
        # // Compute integer values (correction unit is 732ug/count)
        shiftX = -round(self._calibAccXOfs / 0.000732)
        if shiftX < 0:
            shiftX = shiftX + 65536
        shiftY = -round(self._calibAccYOfs / 0.000732)
        if shiftY < 0:
            shiftY = shiftY + 65536
        shiftZ = -round(self._calibAccZOfs / 0.000732)
        if shiftZ < 0:
            shiftZ = shiftZ + 65536
        scaleX = round(2048.0 / self._calibAccXScale) - 2048
        scaleY = round(2048.0 / self._calibAccYScale) - 2048
        scaleZ = round(2048.0 / self._calibAccZScale) - 2048
        if scaleX < -2048 or scaleX >= 2048 or scaleY < -2048 or scaleY >= 2048 or scaleZ < -2048 or scaleZ >= 2048:
            scaleExp = 3
            if scaleX < -1024 or scaleX >= 1024 or scaleY < -1024 or scaleY >= 1024 or scaleZ < -1024 or scaleZ >= 1024:
                scaleExp = 2
                if scaleX < -512 or scaleX >= 512 or scaleY < -512 or scaleY >= 512 or scaleZ < -512 or scaleZ >= 512:
                    scaleExp = 1
                else:
                    scaleExp = 0
        if scaleExp > 0:
            scaleX = ((scaleX) >> (scaleExp))
            scaleY = ((scaleY) >> (scaleExp))
            scaleZ = ((scaleZ) >> (scaleExp))
        if scaleX < 0:
            scaleX = scaleX + 1024
        if scaleY < 0:
            scaleY = scaleY + 1024
        if scaleZ < 0:
            scaleZ = scaleZ + 1024
        scaleLo = ((((scaleY) & (15))) << (12)) + ((scaleX) << (2)) + scaleExp
        scaleHi = ((scaleZ) << (6)) + ((scaleY) >> (4))
        
        # // Save calibration parameters
        newcalib = "5," + str(int(shiftX)) + "," + str(int(shiftY)) + "," + str(int(shiftZ)) + "," + str(int(scaleLo)) + "," + str(int(scaleHi))
        self._calibStage = 0
        return self.set_calibrationParam(newcalib)

    def cancel3DCalibration(self):
        """
        Aborts the sensors tridimensional calibration process et restores normal settings.
        
        On failure, throws an exception or returns a negative error code.
        """
        if self._calibStage == 0:
            return YAPI.SUCCESS
        # // may throw an exception
        self._calibStage = 0
        return self.set_calibrationParam(self._calibSavedParams)

    def nextRefFrame(self):
        """
        Continues the enumeration of reference frames started using yFirstRefFrame().
        
        @return a pointer to a YRefFrame object, corresponding to
                a reference frame currently online, or a None pointer
                if there are no more reference frames to enumerate.
        """
        hwidRef = YRefParam()
        if YAPI.YISERR(self._nextFunction(hwidRef)):
            return None
        if hwidRef.value == "":
            return None
        return YRefFrame.FindRefFrame(hwidRef.value)

#--- (end of YRefFrame implementation)

#--- (RefFrame functions)

    @staticmethod
    def FirstRefFrame():
        """
        Starts the enumeration of reference frames currently accessible.
        Use the method YRefFrame.nextRefFrame() to iterate on
        next reference frames.
        
        @return a pointer to a YRefFrame object, corresponding to
                the first reference frame currently online, or a None pointer
                if there are none.
        """
        devRef = YRefParam()
        neededsizeRef = YRefParam()
        serialRef = YRefParam()
        funcIdRef = YRefParam()
        funcNameRef = YRefParam()
        funcValRef = YRefParam()
        errmsgRef = YRefParam()
        size = YAPI.C_INTSIZE
        #noinspection PyTypeChecker,PyCallingNonCallable
        p = (ctypes.c_int * 1)()
        err = YAPI.apiGetFunctionsByClass("RefFrame", 0, p, size, neededsizeRef, errmsgRef)

        if YAPI.YISERR(err) or not neededsizeRef.value:
            return None

        if YAPI.YISERR(
                YAPI.yapiGetFunctionInfo(p[0], devRef, serialRef, funcIdRef, funcNameRef, funcValRef, errmsgRef)):
            return None

        return YRefFrame.FindRefFrame(serialRef.value + "." + funcIdRef.value)

#--- (end of RefFrame functions)