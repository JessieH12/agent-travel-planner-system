package com.travel.exception;

/**
 * 自定义业务异常类：用于表示业务逻辑中的异常情况。
 */
public class TravelValidationException extends RuntimeException {
    public TravelValidationException(String message) {
        super(message);
    }
}
