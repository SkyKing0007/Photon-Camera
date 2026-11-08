package android.util;
public class Range<T> { private final T lo,hi; public Range(T lo,T hi){this.lo=lo;this.hi=hi;} public T getLower(){return lo;} public T getUpper(){return hi;} }
